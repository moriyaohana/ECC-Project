from OFDM import OFDM
import numpy as np
from symbol import OFDMSymbol
from reedsolo import RSCodec, ReedSolomonError
from utils import *


class Receiver(object):
    def __init__(self,
                 symbol_weight: int,
                 symbol_size: int,
                 samples_per_symbol: int,
                 sample_rate_hz: float,
                 frequency_range_start_hz: float,
                 frequency_range_end_hz: float,
                 ecc_codec: RSCodec,
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
        self._preamble_retries = 0
        self._ecc_codec = ecc_codec

    @property
    def sync_preamble(self) -> list[float]:
        return self._modulation.sync_preamble

    @property
    def last_symbol(self) -> None | OFDMSymbol:
        if not self._is_synced or len(self._buffer) < 4096:
            return None

        return self._modulation.signal_to_symbols(self._buffer[-4096:])[0]

    def _detect_preamble(self) -> tuple[int, float] | tuple[None, None]:
        correlation = normalized_correlation(np.array(self._buffer[self._last_sync_location:]),
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
        if self._preamble_retries >= 3:
            return

        if self._is_synced:
            self._preamble_retries += 1

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

    def _decode_message(self, encoded_data: bytes, erasures: set[int]):
        corrected_message = encoded_data
        try:
            corrected_message, _, errata = self._ecc_codec.decode(encoded_data, erase_pos=erasures, only_erasures=True)
        except ReedSolomonError:
            print(f"No errors corrected by only correcting erasures! Erasures: {len(erasures)}")

        try:
            corrected_message, _, errata = self._ecc_codec.decode(encoded_data, erase_pos=erasures)
        except ReedSolomonError:
            print(f"No errors corrected even when attempting to correct errors and erasures")

        return corrected_message

    def get_message_symbols(self) -> list[OFDMSymbol]:
        if not self._is_synced:
            return list()

        return self._modulation.signal_to_symbols(list(self._buffer))

    def get_message_data(self) -> tuple[bytes, set[int]]:
        if not self._is_synced:
            return bytes(), set()

        return self._decode_message(*self._modulation.signal_to_data(list(self._buffer)))

    def receive_buffer(self, signal: list[float]) -> None:
        if self._preamble_offset > 0:
            signal = signal[self._preamble_offset:]
            self._preamble_offset = 0
        self._buffer = np.append(self._buffer, signal)
        self._try_sync()
