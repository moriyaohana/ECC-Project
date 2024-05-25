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

    def _detect_preamble(self) -> Optional[int]:
        correlation = self.normalized_correlation(np.array(self._buffer),
                                                  np.array(self._sync_preamble))
        peak_value = np.max(correlation)
        if peak_value > self.CORRELATION_THRESHOLD:
            return np.argmax(correlation)

        return None

    def _try_sync(self):
        if self._is_synced:
            return

        buffer_size_to_keep = 2 * self._modulation.num_samples
        self._buffer = self._buffer[-buffer_size_to_keep:]

        preamble_location = self._detect_preamble()
        if preamble_location is None:
            return

        self._is_synced = True
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
        normalized_signal = (signal - np.mean(signal)) / np.std(signal)
        normalized_preamble = (preamble - np.mean(preamble)) / np.std(preamble)

        return np.correlate(normalized_signal, normalized_preamble, mode='valid') / min(len(signal), len(preamble))
