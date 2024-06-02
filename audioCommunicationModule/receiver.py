from OFDM import OFDM
import numpy as np
from symbol import OFDMSymbol
from utils import *


class Receiver(object):
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

    @property
    def sync_preamble(self) -> list[float]:
        return self._modulation.sync_preamble

    def _detect_preamble(self) -> tuple[int, float] | tuple[None, None]:
        correlation = self.normalized_correlation(np.array(self._buffer[self._last_sync_location:]),
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
    def normalized_correlation(signal: np.ndarray, preamble: np.ndarray) -> np.ndarray:
        if len(signal) < len(preamble):
            return np.array([])
        rolling_std_of_signal = rolling_std(signal, len(preamble))
        normalized_preamble = preamble / np.std(preamble)
        correlation = np.correlate(signal, normalized_preamble) / (rolling_std_of_signal * len(preamble))

        return correlation
