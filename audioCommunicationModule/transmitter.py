from OFDM import OFDM
from reedsolo import RSCodec
from typing import List
from utils import signal_to_pcm


class Transmitter(object):
    def __init__(self,
                 symbol_weight: int,
                 symbol_size: int,
                 samples_per_symbol: int,
                 sample_rate_hz: float,
                 frequency_range_start_hz: float,
                 frequency_range_end_hz: float,
                 ecc_symbols: int,
                 ecc_block: int,
                 snr_threshold: float = 1,
                 sync_preamble_retries: int = 1):
        self._modulation = OFDM(symbol_weight,
                                symbol_size,
                                samples_per_symbol,
                                sample_rate_hz,
                                frequency_range_start_hz,
                                frequency_range_end_hz,
                                snr_threshold)
        self._preamble_retries = sync_preamble_retries
        self._ecc_codec = RSCodec(ecc_symbols, ecc_block)

    def transmit_signal(self, buffer: bytes) -> List[float]:
        message_signal = (
                (self._preamble_retries * self._modulation.sync_preamble) +
                self._modulation.data_to_signal(self._ecc_codec.encode(buffer), terminate=True))

        return message_signal

    def transmit_pcm_data(self, buffer: bytes) -> bytes:
        return signal_to_pcm(self.transmit_signal(buffer))
