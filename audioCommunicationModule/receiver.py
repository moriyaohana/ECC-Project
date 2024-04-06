import numpy as np
from text_over_sound import TextOverSound
from typing import Optional


class Receiver(object):
    CORRELATION_THRESHOLD = 0.5

    def __init__(self, text_over_sound: TextOverSound, sync_preamble: np.array):
        self._text_over_sound = text_over_sound
        self._is_synced: bool = False
        self._sync_preamble: np.array = sync_preamble
        self._buffer: np.array = np.array([])

    def _detect_preamble(self) -> Optional[int]:
        correlation = np.correlate(self._buffer,
                                   self._sync_preamble,
                                   mode='valid')
        peak_value = np.max(correlation)
        if peak_value > self.CORRELATION_THRESHOLD:
            return np.argmax(correlation)

        return None

    def _try_sync(self):
        if self._is_synced:
            return

        buffer_size_to_keep = 2 * self._text_over_sound.num_samples
        self._buffer = self._buffer[-buffer_size_to_keep:]

        preamble_location = self._detect_preamble()
        if preamble_location is None:
            return

        self._is_synced = True
        self._buffer = self._buffer[preamble_location + len(self._sync_preamble):]

    def get_message(self) -> str:
        if not self._is_synced:
            return str()
        return self._text_over_sound.pcm_to_string(self._buffer.tobytes())

    def receive_buffer(self, pcm_data: bytes) -> None:
        self._buffer = np.append(self._buffer, self._text_over_sound.pcm_to_signal(pcm_data))
        self._try_sync()

    @staticmethod
    def normalized_correlation(signal: np.array, preamble: np.array) -> np.ndarray:
        normalized_signal = (signal - np.mean(signal)) / np.std(signal)
        normalized_preamble = (preamble - np.mean(preamble)) / np.std(preamble)

        return np.correlate(normalized_signal, normalized_preamble, mode='valid') / min(len(signal), len(preamble))
