import numpy as np

from symbol_map import SymbolMap
from OFDM import OFDM
from utils import *


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

    def char_to_pcm_data(self, char: str) -> bytes:
        return signal_to_pcm(self._modulation._symbol_to_signal(self._char_symbol_map.char_to_symbol(char)))

    def pcm_to_char(self, pcm_data: bytes) -> str:
        return self._char_symbol_map.symbol_to_char(self._modulation._signal_to_symbol(pcm_to_signal(pcm_data)))

    def pcm_to_string(self, pcm_data: bytes) -> str:
        message = str()
        for symbol_data_index in range(0, len(pcm_data), 2 * self._num_samples):
            symbol_pcm_data = pcm_data[symbol_data_index: symbol_data_index + 2 * self._num_samples]
            message += self.pcm_to_char(symbol_pcm_data)

        return message
