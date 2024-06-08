import random

# noinspection PyUnresolvedReferences
import numpy as np
from typing import Optional
from symbol import OFDMSymbol
from symbol_map import SymbolMap
from utils import *
from scipy.signal import chirp


class OFDM(object):
    def __init__(self,
                 symbol_weight: int,
                 symbol_size: int,
                 samples_per_symbol: int,
                 sample_rate_hz: float,
                 frequency_range_start_hz: float,
                 frequency_range_end_hz: float,
                 snr_threshold: float = 1):
        self._symbol_weight = symbol_weight
        self._symbol_size = symbol_size
        self._samples_per_symbol = samples_per_symbol
        self._sample_rate_hz = sample_rate_hz
        self._frequency_range_start_hz = frequency_range_start_hz
        self._frequency_range_end_hz = frequency_range_end_hz
        self._duration_sec = samples_per_symbol / sample_rate_hz
        self._frequencies = self._get_frequencies(
            frequency_range_start_hz,
            frequency_range_end_hz,
            symbol_size,
            sample_rate_hz,
            samples_per_symbol)
        self._snr_threshold = snr_threshold
        self._symbol_map = SymbolMap(symbol_size, symbol_weight)
        self._sync_preamble = self._generate_chip_signal()

    @property
    def samples_per_symbol(self):
        return self._samples_per_symbol

    def _generate_chip_signal(self):
        time_sequence = np.linspace(0, self._duration_sec, self._samples_per_symbol)

        return list(chirp(time_sequence,
                          f0=self._frequency_range_start_hz,
                          f1=self._frequency_range_end_hz,
                          t1=time_sequence[-1],
                          method="linear"))

    @property
    def sample_rate_hz(self):
        return self._sample_rate_hz

    @property
    def frequencies_hz(self):
        return self._frequencies

    @property
    def sync_preamble(self):
        return self._sync_preamble

    @property
    def termination_symbol(self):
        return self._symbol_map.termination_symbol

    @staticmethod
    def _get_step(start_range_hz: float, end_range_hz: float, symbol_size: int, sample_rate_hz: float,
                  num_samples: int) -> float:
        diff = sample_rate_hz / num_samples
        i = 1
        step = 0
        end = 0
        while end <= end_range_hz:
            step = i * diff
            end = start_range_hz + (symbol_size - 1) * step
            i += 1
        return step - diff

    @staticmethod
    def _get_frequencies(start_range_hz: float, end_range_hz: float, symbol_size: int, sample_rate_hz: float,
                         num_samples: int) -> list[float]:
        if symbol_size <= 1:
            raise ValueError("The size of the array (symbol_size) must be greater than 1.")

        step = OFDM._get_step(start_range_hz, end_range_hz, symbol_size, sample_rate_hz, num_samples)

        # Use a list comprehension to generate the array
        frequencies = [start_range_hz + index * step for index in range(symbol_size)]

        return frequencies

    def _top_frequencies(self, signal: list[float]) -> list[tuple[float, float]]:
        frequencies = signal_fft(signal, self._sample_rate_hz)
        frequencies = [(freq, amp) for freq, amp in frequencies if freq in self._frequencies]

        MAGNITUDE_INDEX = 1
        sorted_frequencies = sorted(frequencies, key=lambda item: item[MAGNITUDE_INDEX], reverse=True)

        return sorted_frequencies[:self._symbol_weight + 1]

    def _signal_to_symbol(self, signal: list[float]) -> Optional[OFDMSymbol]:
        if len(signal) != self._samples_per_symbol:
            raise RuntimeError('Unexpected signal length.'
                               f'Expected {self._samples_per_symbol} but got {len(signal)}')
        top_frequencies = self._top_frequencies(signal)

        MAGNITUDE_INDEX = 1
        if (top_frequencies[self._symbol_weight - 1][MAGNITUDE_INDEX] /
                top_frequencies[self._symbol_weight][MAGNITUDE_INDEX] < self._snr_threshold):
            return None

        present_frequencies = {
            self._frequencies.index(frequency) for
            frequency, magnitude in
            top_frequencies[:self._symbol_weight]}

        return OFDMSymbol(present_frequencies)

    def signal_to_symbols(self, signal: list[float]) -> list[OFDMSymbol]:
        if len(signal) % self._samples_per_symbol != 0:
            signal = signal + [0] * (self._samples_per_symbol - len(signal) % self._samples_per_symbol)

        message = []
        for signal_data_index in range(0, len(signal), self._samples_per_symbol):
            signal_chunk = signal[signal_data_index:signal_data_index + self._samples_per_symbol]
            message.append(self._signal_to_symbol(signal_chunk))

        return message

    # TODO: This is a work-in-progress mess that needs to be redone
    def _remove_preamble_from_signal(self, signal: list[float]) -> list[float]:
        new_signal = []
        removed = 0
        for signal_data_index in range(0, len(signal), self._samples_per_symbol):
            signal_chunk = signal[signal_data_index:signal_data_index + self._samples_per_symbol]
            correlation = normalized_correlation(signal_chunk, self.sync_preamble)
            if len(correlation) == 0:
                new_signal += signal_chunk
                continue
            assert len(correlation) == 1
            correlation = correlation[0]
            if correlation < 0.7 or removed > 2:
                new_signal += signal_chunk
            removed += 1

        return new_signal

    def signal_to_data(self, signal: list[float]) -> tuple[bytes, set[int]]:
        signal = self._remove_preamble_from_signal(signal)
        symbols = self.signal_to_symbols(signal)
        try:
            symbols.remove(self._symbol_map.termination_symbol)
            symbols.remove(self._symbol_map.sync_symbol)
        except ValueError:
            pass

        return self._symbol_map.symbols_to_bytes(symbols)

    def _symbol_to_signal(self, symbol: OFDMSymbol) -> list[float]:
        PADDING_LENGTH = self._samples_per_symbol // 16
        padding_data = [0] * PADDING_LENGTH
        data_length = self._samples_per_symbol - 2 * PADDING_LENGTH
        return (padding_data +
                inverse_fft(symbol.frequencies(self._frequencies), data_length, self._sample_rate_hz) +
                padding_data)

    def symbols_to_signal(self, symbols: OFDMSymbol | list[OFDMSymbol]) -> list[float]:
        if not isinstance(symbols, list):
            symbols = [symbols]
        signal = []

        for symbol in symbols:
            signal += self._symbol_to_signal(symbol)

        return signal

    def data_to_signal(self, data: bytes) -> list[float]:
        return self.symbols_to_signal(self._symbol_map.bytes_to_symbols(data))
