import numpy as np

from char_symbol_map import CharSymbolMap

import matplotlib.pyplot as plt


class TextOverSound:
    """
    This class is responsible for translating text to an audio signals,
    with given range of frequencies and symbol length.

    """
    _symbol_weight: int
    _symbol_size: int
    _frequencies: list[float]
    _duration_millis: float
    _sample_rate_khz: float

    def __init__(self,
                 num_samples: int,
                 start_range_frequencies_khz: float,
                 end_range_frequencies_khz: float,
                 symbol_size: int,
                 symbol_weight: int,
                 sample_rate_khz: float = 16
                 ):
        self._num_samples = num_samples
        self._sample_rate_khz = sample_rate_khz
        self._duration_millis = num_samples / sample_rate_khz
        self._frequencies = self.get_frequencies(start_range_frequencies_khz,
                                                 end_range_frequencies_khz,
                                                 symbol_size,
                                                 sample_rate_khz,
                                                 num_samples)
        self._symbol_size = symbol_size
        self._symbol_weight = symbol_weight
        self._char_symbol_map = CharSymbolMap(symbol_size, symbol_weight)
    @property
    def sample_rate_khz(self):
        return self._sample_rate_khz

    @staticmethod
    def get_step(
            start_range_khz: float,
            end_range_khz: float,
            symbol_size: int,
            sample_rate_khz: float,
            num_samples: int) -> float:

        diff = sample_rate_khz / num_samples
        i = 1
        step = 0
        end = 0
        while end <= end_range_khz:
            step = i * diff
            end = start_range_khz + (symbol_size - 1) * step
            i += 1
        return step - diff

    # CR: Should this be private?
    @staticmethod
    def get_frequencies(start_range_khz: float,
                        end_range_khz: float,
                        symbol_size: int,
                        sample_rate_khz: float,
                        num_samples: int) -> list[float]:
        if symbol_size <= 1:
            raise ValueError("The size of the array (symbol_size) must be greater than 1.")

        step = TextOverSound.get_step(start_range_khz, end_range_khz, symbol_size, sample_rate_khz, num_samples)

        # Use a list comprehension to generate the array
        frequencies = [start_range_khz + index * step for index in range(symbol_size)]

        return frequencies

    def string_to_pcm_data(self, string: str) -> bytes:
        pcm_data = bytes()
        for char in string:
            pcm_data += self.char_to_pcm_data(char)

        return pcm_data

    def get_inverse_fft(self,
                        frequencies_khz: list[float]) -> list[float]:
        sum_of_sin = []
        for time_step in range(self._num_samples):  # num_samples is representing desecrate time axis t[s]

            sin_values = [np.sin(2 * np.pi * frequency * time_step / self._sample_rate_khz) for frequency in frequencies_khz ]

            sample = sum(sin_values)
            sum_of_sin.append(sample)

        return sum_of_sin

    def get_char_selected_frequencies(self, char: str) -> list[float]:
        if len(char) != 1:
            raise ValueError("The size of the string (char) must be equal to 1.")

        presence_array = self._char_symbol_map.char_to_symbol(char)

        selected_frequencies = [frequency for
                                (index, frequency) in
                                enumerate(self._frequencies) if
                                presence_array[index] == 1]
        return selected_frequencies

    def char_to_pcm_data(self, char: str) -> bytes:
        selected_frequencies = self.get_char_selected_frequencies(char)
        signal = self.get_inverse_fft(selected_frequencies)

        # 32767 is the maximum value for 16-bit signed integer
        # sound is represented by a 16 bit value PCM16 (sound format)
        PCM_16BIT_MAXIMUM_VALUE = 32767 / self._symbol_weight
        pcm_data = np.array([int(sample * PCM_16BIT_MAXIMUM_VALUE) for sample in signal], dtype=np.int16)

        return pcm_data.tobytes()

    def plot_pcm_fft(self, pcm_data: bytes) -> None:
        f, fft_pcm = self.pcm_fft(pcm_data)
        plt.plot(f, np.abs(fft_pcm))

        plt.title('FFT Result freq')
        plt.xlabel('frequency (Hz)')
        plt.ylabel('Amplitude')

    # plot: the signal
    def plot_signal_per_char(self, char: str) -> None:
        # PerformFFT
        selected_frequencies = self.get_char_selected_frequencies(char)
        signal = self.get_inverse_fft(selected_frequencies)

        self.plot_signal(signal)

    def pcm_to_signal(self, pcm_data: bytes) -> np.ndarray:
        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)

        PCM_16BIT_MAXIMUM_VALUE = 32767.0 / self._symbol_weight
        return pcm_array / PCM_16BIT_MAXIMUM_VALUE

    def plot_signal(self, signal):
        t = np.linspace(0, self._duration_millis, int(self._sample_rate_khz * self._duration_millis), endpoint=False)

        plt.plot(t[:len(t) // 10], signal[:len(signal) // 10])
        plt.title('Original Signal')
        plt.xlabel('Time (ms)')
        plt.ylabel('Amplitude')

    def pcm_fft(self, pcm_data: bytes) -> tuple[np.ndarray, np.ndarray]:
        signal = self.pcm_to_signal(pcm_data)

        # getting the magnitude of positive frequencies
        signal_fft = np.fft.fft(signal)[:self._num_samples // 2]
        f = np.fft.fftfreq(self._num_samples, 1 / self.sample_rate_khz)[:self._num_samples // 2]

        return f, np.abs(signal_fft)

    def pcm_top_frequencies(self, pcm_data: bytes) -> list[tuple[float, float]]:
        # getting (symbol_weight+1) dominant frequencies
        MAGNITUDE_INDEX = 1
        f, magnitude = self.pcm_fft(pcm_data)
        sorted_frequencies = sorted(zip(f, magnitude), key=lambda item: item[MAGNITUDE_INDEX], reverse=True)

        return sorted_frequencies[:self._symbol_weight + 1]

    def pcm_to_char(self, pcm_data: bytes) -> str:
        top_frequencies = self.pcm_top_frequencies(pcm_data)
        present_array = [0 for _ in range(self._symbol_size)]
        for frequency, _ in top_frequencies[:-1]:
            present_array[self._frequencies.index(frequency)] = 1

        return self._char_symbol_map.symbol_to_char(present_array)




