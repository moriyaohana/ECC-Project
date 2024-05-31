import numpy as np
from OFDM import OFDM
from symbol import OFDMSymbol
from typing import Optional


class Receiver(object):
    CORRELATION_THRESHOLD = 0.8

    def __init__(self, modulation: OFDM, sync_preamble: list[float]):
        self._modulation = modulation
        self._is_synced: bool = False
        self._sync_preamble: list[float] = sync_preamble
        self._buffer: list[float] = []
        self._preamble_offset: int = 0
        self._last_sync_location: int = 0
        self._sync_score: int = 0

    def _detect_preamble(self) -> tuple[int, float] | tuple[None, None]:
        correlation = self.normalized_correlation(np.array(self._buffer[self._last_sync_location:]),
                                                  np.array(self._sync_preamble))
        if len(correlation) == 0:
            return None, None
        peak_value = np.max(correlation)
        if peak_value > self.CORRELATION_THRESHOLD:
            return np.argmax(correlation), max(correlation)

        return None, None

    def resync(self, new_sync_location: int, new_sync_score: int):
        if new_sync_location > self._sync_score:
            self._sync_score = new_sync_score
            self._last_sync_location = new_sync_location
            self._buffer = self._buffer[new_sync_location + len(self._sync_preamble):]

    def _try_sync(self):
        preamble_location, sync_score = self._detect_preamble()
        if preamble_location is None:
            if not self._is_synced:
                buffer_size_to_keep = 2 * self._modulation.num_samples
                self._buffer = self._buffer[-buffer_size_to_keep:]

            return

        if self._is_synced:
            return self.resync(preamble_location, sync_score)

        self._is_synced = True
        self._sync_score = sync_score
        self._preamble_offset = preamble_location + len(self._sync_preamble) - len(self._buffer)
        self._buffer = self._buffer[preamble_location + len(self._sync_preamble):]

    def get_message(self) -> list[OFDMSymbol]:
        if not self._is_synced:
            return list()

        return self._modulation.signal_to_symbols(list(self._buffer))

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
        normalized_signal = signal / np.std(signal)
        normalized_preamble = preamble / np.std(preamble)

        return np.correlate(normalized_signal, normalized_preamble, mode='valid') / min(len(signal), len(preamble))
