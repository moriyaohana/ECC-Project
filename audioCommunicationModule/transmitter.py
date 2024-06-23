from typing import Optional, Union

import reedsolo

from OFDM import OFDM
from common import default_nsym, default_nsize, default_symbol_size, default_symbol_weight, default_samples_per_symbol, \
    default_sample_rate_hz, default_frequency_range_start_hz, default_frequency_range_end_hz
from symbol import OFDMSymbol
from symbol_map import SymbolMap
from utils import *
import numpy as np


class Transmitter:
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
    def encode_string(string: str):
        byte_data = string.encode("utf-8")
        rscode = reedsolo.RSCodec(nsym=default_nsym, nsize=default_nsize)
        return rscode.encode(byte_data)

    @property
    def modulation(self):
        return self._modulation


def create_transmitter():
    symbol_map = SymbolMap(default_symbol_size, default_symbol_weight)

    transmitter = Transmitter(default_symbol_weight,
                              default_symbol_size,
                              default_samples_per_symbol,
                              default_sample_rate_hz,
                              default_frequency_range_start_hz,
                              default_frequency_range_end_hz,
                              snr_threshold=1.5,
                              correlation_threshold=0.8)

    def message_to_wav(message: str):
        encoded_message = Transmitter.encode_string(message)

        test_signal = 3 * transmitter.sync_preamble + transmitter.modulation.data_to_signal(
            encoded_message) + transmitter.modulation.symbols_to_signal(
            symbol_map.termination_symbol)

        return signal_to_pcm(test_signal)

    return message_to_wav
