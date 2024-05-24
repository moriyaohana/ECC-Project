import numpy as np

from symbol_map import SymbolMap
from OFDM import OFDM
import matplotlib.pyplot as plt


class TextOverSound:
    """
    This class is responsible for translating text to an audio signals,
    with given range of frequencies and symbol length.

    """
    _symbol_weight: int
    _symbol_size: int
    _frequencies: list[float]
    _duration_sec: float
    _sample_rate_hz: float

    def __init__(self, num_samples: int, start_range_frequencies_hz: float, end_range_frequencies_hz: float,
                 symbol_size: int, symbol_weight: int, sample_rate_hz: float = 16):
        self._num_samples = num_samples
        self._sample_rate_hz = sample_rate_hz
        self._duration_sec = num_samples / sample_rate_hz
        self._symbol_size = symbol_size
        self._symbol_weight = symbol_weight
        self._char_symbol_map = SymbolMap(symbol_size, symbol_weight)

        self._modulation = OFDM(
            symbol_weight,
            symbol_size,
            num_samples,
            sample_rate_hz,
            start_range_frequencies_hz,
            end_range_frequencies_hz
        )

    @property
    def num_samples(self):
        return self._num_samples

    @property
    def sample_rate_hz(self):
        return self._sample_rate_hz

    def string_to_pcm_data(self, string: str) -> bytes:
        pcm_data = bytes()
        for char in string:
            pcm_data += self.char_to_pcm_data(char)

        return pcm_data

    def get_char_selected_frequencies(self, char: str) -> list[float]:
        if len(char) != 1:
            raise ValueError("The size of the string (char) must be equal to 1.")

        presence_array = self._char_symbol_map.char_to_symbol(char)

        selected_frequencies = [frequency for (index, frequency) in enumerate(self._frequencies) if
                                presence_array[index] == 1]
        return selected_frequencies

    def signal_to_pcm(self, signal: list[float]) -> bytes:
        # 32767 is the maximum value for 16-bit signed integer
        # sound is represented by a 16 bit value PCM16 (sound format)
        # Normalization by symbol_weight needed to prevent overflow
        PCM_16BIT_MAXIMUM_VALUE = 32767.0# / self._symbol_weight
        pcm_data = np.array([int(sample * PCM_16BIT_MAXIMUM_VALUE) for sample in signal], dtype=np.int16)

        return pcm_data.tobytes()

    def char_to_pcm_data(self, char: str) -> bytes:
        return self.signal_to_pcm(self._modulation.symbol_to_signal(self._char_symbol_map.char_to_symbol(char)))

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

    def pcm_to_signal(self, pcm_data: bytes) -> list[float]:
        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)

        # Normalization by symbol_weight needed to prevent overflow
        PCM_16BIT_MAXIMUM_VALUE = 32767.0# / self._symbol_weight
        return list(pcm_array / PCM_16BIT_MAXIMUM_VALUE)

    def pcm_to_char(self, pcm_data: bytes) -> str:
        return self._char_symbol_map.symbol_to_char(self._modulation.signal_to_symbol(self.pcm_to_signal(pcm_data)))

    def pcm_to_string(self, pcm_data: bytes) -> str:
        message = str()
        for symbol_data_index in range(0, len(pcm_data), 2 * self._num_samples):
            symbol_pcm_data = pcm_data[symbol_data_index: symbol_data_index + 2 * self._num_samples]
            message += self.pcm_to_char(symbol_pcm_data)

        return message
