import numpy as np
from typing import Optional
from symbol import OFDMSymbol

import matplotlib.pyplot as plt

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

    def signal_fft(self, signal: list[float]) -> list[tuple[float, float]]:
        signal_fft = np.fft.fft(signal)[:self._samples_per_symbol // 2]
        sampled_frequencies = np.fft.fftfreq(self._samples_per_symbol, 1 / self._sample_rate_hz)[
                              :self._samples_per_symbol // 2]

        assert (len(signal_fft) == len(sampled_frequencies))

        return zip(sampled_frequencies, np.abs(signal_fft))

    def plot_signal(self, signal):
        t = np.linspace(0, self._duration_sec, int(self._sample_rate_hz * self._duration_sec), endpoint=False)

        plt.plot(t[:len(t) // 10], signal[:len(signal) // 10])
        plt.title('Original Signal')
        plt.xlabel('Time (ms)')
        plt.ylabel('Amplitude')

        plt.show()

    def plot_signal_fft(self, signal: list[float]):
        f, fft = list(zip(*self.signal_fft(signal)))
        plt.plot(f, fft)

        plt.title('FFT Result freq')
        plt.xlabel('frequency (Hz)')
        plt.ylabel('Amplitude')

        plt.show()

    def top_frequencies(self, signal: list[float]) -> list[tuple[float, float]]:
        frequencies = self.signal_fft(signal)

        MAGNITUDE_INDEX = 1
        sorted_frequencies = sorted(frequencies, key=lambda item: item[MAGNITUDE_INDEX], reverse=True)

        return sorted_frequencies[:self._symbol_weight + 1]

    def signal_to_symbol(self, signal: list[float]) -> Optional[OFDMSymbol]:
        top_frequencies = self.top_frequencies(signal)
        MAGNITUDE_INDEX = 1
        if (top_frequencies[self._symbol_weight - 1][MAGNITUDE_INDEX] /
                top_frequencies[self._symbol_weight][MAGNITUDE_INDEX] < self.SNR_THRESHOLD):
            return None

        present_frequencies = {
            self._frequencies.index(frequency) for
            frequency, magnitude in
            top_frequencies[:-1]}

        return OFDMSymbol(present_frequencies)

    def signal_to_symbols(self, signal: list[float]) -> list[OFDMSymbol]:
        message = []
        for signal_data_index in range(0, len(signal), self._samples_per_symbol):
            signal_chunk = signal[signal_data_index:signal_data_index + self._samples_per_symbol]
            message += self.signal_to_symbol(signal_chunk)

        return message

    def inverse_fft(self, frequencies_hz: list[float]) -> list[float]:
        sum_of_sin = []
        for time_step in range(self._samples_per_symbol):  # num_samples is representing desecrate time axis t[s]

            sin_values = [np.sin(2 * np.pi * frequency * time_step / self._sample_rate_hz) for frequency in
                          frequencies_hz]

            sample = sum(sin_values) / self._symbol_weight
            sum_of_sin.append(sample)

        return sum_of_sin

    def symbol_to_signal(self, symbol: OFDMSymbol) -> list[float]:
        if symbol.weight != self._symbol_weight:
            raise RuntimeError('OFDM Symbol of incorrect weight. '
                               f'Expected {self._symbol_weight}, but got {symbol.weight}')

        return self.inverse_fft(symbol.frequencies(self._frequencies))

    def symbols_to_signal(self, symbols: list[OFDMSymbol]) -> list[float]:
        signal = []

        for symbol in symbols:
            signal += self.symbol_to_signal(symbol)

        return signal
