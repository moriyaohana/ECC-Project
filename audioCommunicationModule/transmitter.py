from typing import List

from OFDM import OFDM
from reedsolo import RSCodec

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
                 snr_threshold: float = 1):

        self._modulation = OFDM(symbol_weight,
                                symbol_size,
                                samples_per_symbol,
                                sample_rate_hz,
                                frequency_range_start_hz,
                                frequency_range_end_hz,
                                snr_threshold)
        self._ecc_codec = RSCodec(ecc_symbols, ecc_block)

    def transmit_buffer(self, buffer: bytes) -> List[float]:
        message_signal = (
            self._modulation.sync_preamble +
            self._modulation.data_to_signal(self._ecc_codec.encode(buffer)) +
            self._modulation.sync_preamble)

        return message_signal

    def transmit_pcm_data(self, buffer: bytes) -> bytes:
        return signal_to_pcm(self.transmit_buffer(buffer))
