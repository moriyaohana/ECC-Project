import threading
import time
from typing import Optional, Union

import pyaudio
import reedsolo
import sounddevice as sd

from OFDM import OFDM
from common import default_samples_per_symbol, default_sample_rate_hz, default_nsym, default_nsize
from symbol import OFDMSymbol
from symbol_map import SymbolMap
from utils import *


class Receiver(object):
    def __init__(self,
                 symbol_weight: int,
                 symbol_size: int,
                 samples_per_symbol: int,
                 sample_rate_hz: float,
                 frequency_range_start_hz: float,
                 frequency_range_end_hz: float,
                 snr_threshold: float = 1,
                 correlation_threshold: float = 0.7):

        self._modulation = OFDM(symbol_weight,
                                symbol_size,
                                samples_per_symbol,
                                sample_rate_hz,
                                frequency_range_start_hz,
                                frequency_range_end_hz,
                                snr_threshold)
        self._is_synced: bool = False
        self._buffer: list[float] = []
        self._preamble_offset: int = 0
        self._last_sync_location: int = 0
        self._sync_score: int = 0
        self._correlation_threshold: float = correlation_threshold
        self._preamble_retries = 0

    @property
    def sync_preamble(self) -> list[float]:
        return self._modulation.sync_preamble

    @property
    def last_symbol(self) -> Optional[OFDMSymbol]:
        if not self._is_synced or len(self._buffer) < 4096:
            return None

        return self._modulation.signal_to_symbols(self._buffer[-4096:])[0]

    def _detect_preamble(self) -> Union[tuple[int, float], tuple[None, None]]:
        correlation = normalized_correlation(np.array(self._buffer[self._last_sync_location:]),
                                             np.array(self._modulation.sync_preamble))
        if len(correlation) == 0:
            return None, None
        peak_value = np.max(correlation)
        if peak_value > self._correlation_threshold:
            return np.argmax(correlation), max(correlation)

        return None, None

    def _resync(self, new_sync_location: int, new_sync_score: int):
        if new_sync_score > self._sync_score:
            self._sync_score = new_sync_score
            self._last_sync_location = min(new_sync_location + len(self._modulation.sync_preamble),
                                           len(self._buffer))
            self._buffer = self._buffer[new_sync_location + len(self._modulation.sync_preamble):]

    def _try_sync(self):
        if self._preamble_retries >= 3:
            return

        if self._is_synced:
            self._preamble_retries += 1

        preamble_location, sync_score = self._detect_preamble()
        if preamble_location is None:
            if not self._is_synced:
                buffer_size_to_keep = 2 * self._modulation.samples_per_symbol
                self._buffer = self._buffer[-buffer_size_to_keep:]

            return

        if self._is_synced:
            return self._resync(preamble_location, sync_score)

        self._is_synced = True
        self._sync_score = sync_score
        self._preamble_offset = preamble_location + len(self._modulation.sync_preamble) - len(self._buffer)
        self._buffer = self._buffer[preamble_location + len(self._modulation.sync_preamble):]

    def get_message_symbols(self) -> list[OFDMSymbol]:
        if not self._is_synced:
            return list()

        return self._modulation.signal_to_symbols(list(self._buffer))

    def get_message_data(self) -> tuple[bytes, set[int]]:
        if not self._is_synced:
            return bytes(), set()

        return self._modulation.signal_to_data(list(self._buffer))

    def receive_buffer(self, signal: list[float]) -> None:
        if self._preamble_offset > 0:
            signal = signal[self._preamble_offset:]
            self._preamble_offset = 0
        self._buffer = np.append(self._buffer, signal)
        self._try_sync()

    @staticmethod
    def decode_string(data: bytes, erasures: set[int], default_char: str = "_", should_correct=False):
        decoded_data = data.decode("utf-8", errors="replace")
        org = "".join(default_char if index in erasures else char for index, char in enumerate(decoded_data))
        if not should_correct:
            return org
        rscode = reedsolo.RSCodec(nsym=default_nsym, nsize=default_nsize)
        corrected_message = org
        try:
            corrected_message, _, errata = rscode.decode(data, erase_pos=erasures, only_erasures=True)
        except reedsolo.ReedSolomonError:
            print(f"No errors corrected by only correcting erasures! Erasures: {len(erasures)}")

        try:
            corrected_message, _, errata = rscode.decode(data, erase_pos=erasures)
        except reedsolo.ReedSolomonError:
            print(f"No errors corrected even when attempting to correct errors and erasures")

        print(f"org: {org}")
        print(f"cor: {corrected_message}")
        return corrected_message

    def test_receiver_live(symbol_map: SymbolMap, receiver):
        full_data = bytes()
        recording_event = threading.Event()
        received_message = []

        def signal_handler(input_data: bytes, frame_count: int, time_info, status: sd.CallbackFlags):
            start_time = time.time()
            nonlocal full_data
            nonlocal recording_event
            receiver.receive_buffer(pcm_to_signal(input_data))
            if receiver.last_symbol is not None:
                print(symbol_map.symbols_to_bytes([receiver.last_symbol])[0].decode('ascii', errors='ignore'), end='')
            end_time = time.time()
            # print(f"took {end_time - start_time} secs")
            if receiver.last_symbol == symbol_map.termination_symbol:
                recording_event.set()
                return None, pyaudio.paComplete
            # print(decode_string(*symbol_map.symbols_to_bytes(new_message_symbols)))
            full_data += input_data

            return None, pyaudio.paContinue

        recorder = pyaudio.PyAudio()

        # noinspection PyTypeChecker
        recorder.open(format=recorder.get_format_from_width(2),
                      channels=1,
                      rate=int(default_sample_rate_hz),
                      input=True,
                      frames_per_buffer=default_samples_per_symbol,
                      stream_callback=signal_handler)

        print("Recording...")
        timeout_sec = 40
        recording_event.wait(timeout_sec)
        print("\nStopped recording!")

        recorder.terminate()
        message_signal = np.array(pcm_to_signal(full_data))
        data, erasures = receiver.get_message_data()
        print(
            f"final message: '{Receiver.decode_string(data, erasures, should_correct=True)}' with {len(erasures)} erasures")
        return
