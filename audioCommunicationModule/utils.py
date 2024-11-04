import numpy as np
import crc
from scipy.ndimage.filters import uniform_filter1d
from typing import List, Tuple, Union
from enum import Enum


def signal_to_pcm(signal: List[float]) -> bytes:
    # 32767 is the maximum value for 16-bit signed integer
    # sound is represented by a 16 bit value PCM16 (sound format)
    # Normalization by symbol_weight needed to prevent overflow
    PCM_16BIT_MAXIMUM_VALUE = 32767.0
    pcm_data = np.array([int(sample * PCM_16BIT_MAXIMUM_VALUE) for sample in signal], dtype=np.int16)

    return pcm_data.tobytes()


def pcm_to_signal(pcm_data: bytes) -> List[float]:
    pcm_array = np.frombuffer(pcm_data, dtype=np.int16)

    PCM_16BIT_MAXIMUM_VALUE = 32767.0
    return list(pcm_array / PCM_16BIT_MAXIMUM_VALUE)


def signal_fft(signal: List[float], sample_rate_hz: float) -> List[Tuple[float, float]]:
    fft_magnitudes = np.fft.fft(signal)[:len(signal) // 2]
    sampled_frequencies = np.fft.fftfreq(len(signal), 1 / sample_rate_hz)[
                          :len(signal) // 2]

    assert (len(fft_magnitudes) == len(sampled_frequencies))

    return list(zip(sampled_frequencies, np.abs(fft_magnitudes)))


def inverse_fft(frequencies_hz: List[float], num_samples: int, sample_rate_hz: float) -> List[float]:
    sum_of_sin = []
    for time_step in range(num_samples):  # num_samples is representing discrete time axis t[s]

        sin_values = [np.sin(2 * np.pi * frequency * time_step / sample_rate_hz) for frequency in
                      frequencies_hz]

        sample = sum(sin_values) / len(sin_values)
        sum_of_sin.append(sample)

    return sum_of_sin


def rolling_std(data: np.ndarray, window_size: int) -> np.ndarray:
    rolling_mean = uniform_filter1d(data,
                                    window_size,
                                    mode='constant',
                                    cval=0,
                                    origin=-window_size//2)
    rolling_mean_squares = uniform_filter1d(data*data,
                                            window_size,
                                            mode='constant',
                                            cval=0,
                                            origin=-window_size//2)
    return np.sqrt(rolling_mean_squares - rolling_mean*rolling_mean)[:-window_size + 1]


# TODO: For the Chirp Signal we get a correlation above 1, which is concerning
def normalized_correlation(signal: Union[np.ndarray, list],
                           preamble: Union[np.ndarray, list]) -> np.ndarray:
    if not isinstance(signal, np.ndarray):
        signal = np.array(signal)

    if not isinstance(preamble, np.ndarray):
        preamble = np.array(preamble)

    if len(signal) < len(preamble):
        return np.array([])
    rolling_std_of_signal = rolling_std(signal, len(preamble))
    normalized_preamble = preamble / np.std(preamble)
    correlation = np.correlate(signal, normalized_preamble) / (rolling_std_of_signal *
                                                               len(preamble))

    return correlation


CRC_SIZE = 4
def crc_checksum_bytes(data: bytes) -> bytes:
    return crc.Calculator(crc.Crc32.CRC32).checksum(data).to_bytes(length=CRC_SIZE, byteorder='little')
