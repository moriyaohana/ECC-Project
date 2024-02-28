import numpy as np

from char_symbol_map import CharSymbolMap


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
        self._frequencies = self.get_frequencies(start_range_frequencies_khz, end_range_frequencies_khz, symbol_size)
        self._symbol_size = symbol_size
        self._symbol_weight = symbol_weight

    @staticmethod
    def get_frequencies(start_range: float,
                        end_range: float,
                        symbol_size: int) -> list[float]:
        if symbol_size <= 1:
            raise ValueError("The size of the array (symbol_size) must be greater than 1.")

        step = (end_range - start_range) / (symbol_size - 1)

        # Use a list comprehension to generate the array
        frequencies = [start_range + index * step for index in range(symbol_size)]

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

        MILLISECOND_TO_SECOND_FACTOR = 1 / 1000
        num_samples = int((self._duration_millis * MILLISECOND_TO_SECOND_FACTOR) * self._sample_rate_khz)
        char_symbol_map = CharSymbolMap(self._symbol_size, self._symbol_weight)
        presence_array = char_symbol_map.char_to_symbol(char)

        pcm_data = np.zeros(num_samples, dtype=np.int16)

        for index in range(num_samples):
            sample = sum([np.sin(2 * np.pi * frequency * index / self._sample_rate_khz) for
                          frequency_index, frequency in
                          enumerate(self._frequencies) if
                          presence_array[frequency_index]])

            # 32767 is the maximum value for 16-bit signed integer
            # sound is represented by a 16 bit value PCM16 (sound format)
            PCM_16BIT_MAXIMUM_VALUE = 32767
            pcm_data[index] = int(sample * PCM_16BIT_MAXIMUM_VALUE)

        return pcm_data.tobytes()
