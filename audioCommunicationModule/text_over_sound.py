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
                 duration_millis: float,
                 start_range_frequencies_khz: float,
                 end_range_frequencies_khz: float,
                 symbol_size: int,
                 symbol_weight: int,
                 sample_rate_khz: float = 16
                 ):
        self._sample_rate_khz = sample_rate_khz
        self._duration_millis = duration_millis
        self._frequencies = self.get_frequencies(start_range_frequencies_khz,
                                                 end_range_frequencies_khz,
                                                 symbol_size,
                                                 sample_rate_khz)
        self._symbol_size = symbol_size
        self._symbol_weight = symbol_weight

    @property
    def sample_rate_khz(self):
        return self._sample_rate_khz

    # CR: Should this be private?
    # CR: why should we work in given range if the range set by: start_range,
    #     symbol_size and sample_rate ?
    @staticmethod
    def get_frequencies(start_range_khz: float,
                        end_range_khz: float,
                        symbol_size: int,
                        sample_rate_khz) -> list[float]:
        if symbol_size <= 1:
            raise ValueError("The size of the array (symbol_size) must be greater than 1.")

        step = sample_rate_khz / float(symbol_size)

        # Use a list comprehension to generate the array
        frequencies = [start_range_khz + index * step for index in range(symbol_size)]

        return frequencies

    def string_to_pcm_data(self, string: str) -> bytes:
        pcm_data = bytes()
        for char in string:
            pcm_data += self.char_to_pcm_data(char)

        return pcm_data

    def char_to_pcm_data(self, char: str) -> bytes:
        # num_samples is representing desecrate time axis t[s]
        if len(char) != 1:
            raise ValueError("The size of the string (char) must be equal to 1.")

        num_samples = int(self._duration_millis * self._sample_rate_khz)

        # CR: Why are you initializing this for each call to the function? Do the parameters change?
        char_symbol_map = CharSymbolMap(self._symbol_size, self._symbol_weight)
        presence_array = char_symbol_map.char_to_symbol(char)

        pcm_data = np.zeros(num_samples, dtype=np.int16)
    # CR: index to
        sample = 0
        for index in range(num_samples):
            sample = sum([np.sin(2 * np.pi * frequency * index / self._sample_rate_khz) for
                          frequency_index, frequency in
                          enumerate(self._frequencies) if
                          presence_array[frequency_index]])

            # 32767 is the maximum value for 16-bit signed integer
            # sound is represented by a 16 bit value PCM16 (sound format)
            PCM_16BIT_MAXIMUM_VALUE = 32767
            pcm_data[index] = int(sample * PCM_16BIT_MAXIMUM_VALUE)
        # CR: plot the abs of the fft of pcm_data

        # Perform Inverse FFT
        inverse_fft_result = np.fft.ifft(pcm_data)

        # Plot the original signal and the result of inverse FFT
        time_axis = (np.arange(num_samples) / self._sample_rate_khz)
        t = np.linspace(0, self._duration_millis, int(self._sample_rate_khz * self._duration_millis), endpoint=False)
        plt.figure(figsize=(12, 6))

        plt.subplot(2, 1, 1)
        plt.plot(t[:len(t) // 10], pcm_data[:len(pcm_data) // 10])
        plt.title('Original Signal')
        plt.xlabel('Time (ms)')
        plt.ylabel('Amplitude')



        plt.subplot(2, 1, 2)
        plt.plot(t[:len(t) // 10], np.real(inverse_fft_result)[:len(pcm_data) // 10])  # Use np.real() to extract the real part of the complex result
        plt.title('Inverse FFT Result')
        plt.xlabel('Time (ms)')
        plt.ylabel('Amplitude')

        plt.tight_layout()
        plt.show()

        return pcm_data.tobytes()
