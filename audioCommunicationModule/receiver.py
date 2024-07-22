from typing import List, Optional, Tuple, Union, Set

from OFDM import OFDM
import numpy as np
from symbol import OFDMSymbol
from reedsolo import RSCodec, ReedSolomonError
from utils import *


class Receiver(object):
    def __init__(self,
                 symbol_weight: int,
                 symbol_size: int,
                 samples_per_symbol: int,
                 sample_rate_hz: float,
                 frequency_range_start_hz: float,
                 frequency_range_end_hz: float,
                 ecc_symbols: int,
                 ecc_block: int,
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
        self._buffer: List[float] = []
        self._preamble_offset: int = 0
        self._last_sync_location: int = 0
        self._sync_score: int = 0
        self._correlation_threshold: float = correlation_threshold
        self._preamble_retries = 0
        self._ecc_codec = RSCodec(ecc_symbols, ecc_block)
        self._message_history: List[Tuple[bytes, Set[int], bytes]] = []

    @property
    def sync_preamble(self) -> List[float]:
        return self._modulation.sync_preamble

    @property
    def last_symbol(self) -> Union[None, OFDMSymbol]:
        if not self._is_synced or len(self._buffer) < 4096:
            return None

        return self._modulation.signal_to_symbols(self._buffer[-4096:])[0]

    @property
    def message_history(self):
        return self._message_history

    @property
    def is_synchronised(self):
        return self._is_synced

    def _detect_preamble(self) -> Union[Tuple[int, float], Tuple[None, None]]:
        return self._detect_preamble_in_buffer(self._buffer[self._last_sync_location:])

    def _try_sync(self):
        if self._is_synced:
            return

        preamble_location, sync_score = self._detect_preamble()
        if preamble_location is None:
            if not self._is_synced:
                buffer_size_to_keep = 2 * self._modulation.samples_per_symbol
                self._buffer = self._buffer[-buffer_size_to_keep:]

            return

        self._is_synced = True
        self._sync_score = sync_score
        self._preamble_offset = preamble_location + len(self._modulation.sync_preamble) - len(self._buffer)
        self._buffer = self._buffer[preamble_location + len(self._modulation.sync_preamble):]

    def _decode_message(self, encoded_data: bytes, erasures: Set[int]):
        corrected_message = encoded_data
        errata = erasures
        try:
            corrected_message, _, errata = self._ecc_codec.decode(encoded_data, erase_pos=erasures, only_erasures=True)
        except ReedSolomonError:
            print(f"No errors corrected by only correcting erasures! Erasures: {len(erasures)}")

        try:
            corrected_message, _, errata = self._ecc_codec.decode(encoded_data, erase_pos=erasures)
        except ReedSolomonError:
            print(f"No errors corrected even when attempting to correct errors and erasures")

        return corrected_message, errata

    def get_message_symbols(self) -> List[OFDMSymbol]:
        if not self._is_synced:
            return list()

        return self._modulation.signal_to_symbols(list(self._buffer))

    def get_message_data(self) -> Tuple[bytes, Set[int], bytes]:
        if not self._is_synced:
            return bytes(), set(), bytes()

        raw_message, errors = self._modulation.signal_to_data(list(self._buffer))
        print(raw_message)
        print(errors)
        decoded_message, errata = self._decode_message(raw_message, errors)

        return raw_message, errata, decoded_message

    def receive_buffer(self, signal: List[float]) -> None:
        if self._preamble_offset > 0:
            signal = signal[self._preamble_offset:]
            self._preamble_offset = 0
        self._buffer = np.append(self._buffer, signal)

        potential_termination_index = - 2 * len(self.sync_preamble)
        termination_location, _ = self._detect_preamble_in_buffer(self._buffer[potential_termination_index:])
        if self._is_synced and termination_location is not None:
            self._buffer = self._buffer[: potential_termination_index + termination_location]
            self._terminate_message()

        self._try_sync()

    def receive_pcm16_buffer(self, pcm_data: List[int]) -> None:
        pcm_data_bytes = np.array(pcm_data, dtype=np.int16).tobytes()
        return self.receive_buffer(pcm_to_signal(pcm_data_bytes))

    def _terminate_message(self):
        current_message, current_errors, decoded_message = self.get_message_data()
        self._message_history.append(
            (current_message,
             current_errors,
             decoded_message)
        )
        self._preamble_offset = 0
        self._preamble_retries = 0
        self._last_sync_location = 0
        self._buffer = []
        self._is_synced = False

    def _detect_preamble_in_buffer(self, buffer: List[float]) -> Union[Tuple[int, float], Tuple[None, None]]:
        correlation = normalized_correlation(buffer,
                                             self._modulation.sync_preamble)
        if len(correlation) == 0:
            return None, None
        peak_value = abs(np.max(correlation))

        if peak_value > self._correlation_threshold:
            return np.argmax(correlation), max(correlation)

        return None, None
