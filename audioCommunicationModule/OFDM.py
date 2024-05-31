import numpy as np
from typing import Optional
from symbol import OFDMSymbol
from utils import *


class OFDM(object):
    SNR_THRESHOLD = 1  # TODO: Set to something sensible

    _symbol_weight: int
    _symbol_size: int
    _frequencies: list[float]
    _sample_rate_hz: float

    def __init__(self, symbol_weight: int, symbol_size: int, samples_per_symbol: int, sample_rate_hz: float,
                 frequency_range_start_hz, frequency_range_end_hz):
        self._symbol_weight = symbol_weight
        self._symbol_size = symbol_size
        self._samples_per_symbol = samples_per_symbol
        self._sample_rate_hz = sample_rate_hz
        self._frequency_range_start_hz = frequency_range_start_hz
        self._frequency_range_end_hz = frequency_range_end_hz
        self._duration_sec = samples_per_symbol / sample_rate_hz
        self._frequencies = self.get_frequencies(
            frequency_range_start_hz,
            frequency_range_end_hz,
            symbol_size,
            sample_rate_hz,
            samples_per_symbol)

    @property
    def num_samples(self):
        return self._samples_per_symbol

    @property
    def sample_rate_hz(self):
        return self._sample_rate_hz

    @property
    def frequencies_hz(self):
        return self._frequencies

    @staticmethod
    def get_step(start_range_hz: float, end_range_hz: float, symbol_size: int, sample_rate_hz: float,
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
    def get_frequencies(start_range_hz: float, end_range_hz: float, symbol_size: int, sample_rate_hz: float,
                        num_samples: int) -> list[float]:
        if symbol_size <= 1:
            raise ValueError("The size of the array (symbol_size) must be greater than 1.")

        step = OFDM.get_step(start_range_hz, end_range_hz, symbol_size, sample_rate_hz, num_samples)

        # Use a list comprehension to generate the array
        frequencies = [start_range_hz + index * step for index in range(symbol_size)]

        return frequencies

    def top_frequencies(self, signal: list[float]) -> list[tuple[float, float]]:
        frequencies = signal_fft(signal, self._sample_rate_hz)
        frequencies = [(freq, amp) for freq, amp in frequencies if freq in self._frequencies]

        MAGNITUDE_INDEX = 1
        sorted_frequencies = sorted(frequencies, key=lambda item: item[MAGNITUDE_INDEX], reverse=True)

        return sorted_frequencies[:self._symbol_weight+1]

    def signal_to_symbol(self, signal: list[float]) -> Optional[OFDMSymbol]:
        if len(signal) != self._samples_per_symbol:
            raise RuntimeError('Unexpected signal length.'
                               f'Expected {self._samples_per_symbol} but got {len(signal)}')
        top_frequencies = self.top_frequencies(signal)
        if len(top_frequencies) < self._symbol_weight:
            return None
        MAGNITUDE_INDEX = 1
        # if (top_frequencies[self._symbol_weight - 1][MAGNITUDE_INDEX] /
        #         top_frequencies[self._symbol_weight][MAGNITUDE_INDEX] < self.SNR_THRESHOLD):
        #     return None
        #
        # if not all((frequency in self._frequencies) for frequency, _ in top_frequencies[:-1]):
        #     return None

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
            message.append(self.signal_to_symbol(signal_chunk))

        return message

    def symbol_to_signal(self, symbol: OFDMSymbol) -> list[float]:
        if symbol.weight != self._symbol_weight:
            raise RuntimeError('OFDM Symbol of incorrect weight. '
                               f'Expected {self._symbol_weight}, but got {symbol.weight}')
        PADDING_LENGTH = self._samples_per_symbol // 16
        padding_data = [0] * PADDING_LENGTH
        data_length = self._samples_per_symbol - 2 * PADDING_LENGTH
        return (padding_data +
                inverse_fft(symbol.frequencies(self._frequencies), data_length, self._sample_rate_hz) +
                padding_data)

    def symbols_to_signal(self, symbols: list[OFDMSymbol]) -> list[float]:
        signal = []

        for symbol in symbols:
            signal += self.symbol_to_signal(symbol)

        return signal
