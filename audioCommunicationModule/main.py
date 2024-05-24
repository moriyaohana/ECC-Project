import random

import pyaudio
from text_over_sound import TextOverSound
from symbol_map import SymbolMap
from OFDM import OFDM
from receiver import Receiver
from utils import *
import numpy as np

default_samples_per_symbol = 4096
default_frequency_range_start_hz = 500
default_frequency_range_end_hz = 5_000
default_symbol_size = 16
default_symbol_weight = 3
default_sample_rate_hz = 16_000


def normalized_correlation(signal, preamble):
    signal_pcm = np.frombuffer(signal, dtype=np.int16)
    preamble_pcm = np.frombuffer(preamble, dtype=np.int16)

    normalized_signal_pcm = signal_pcm / np.std(signal_pcm)
    normalized_preamble_pcm = preamble_pcm / np.std(preamble_pcm)

    return np.correlate(normalized_signal_pcm, normalized_preamble_pcm, mode='valid')


def random_frequencies(frequencies_hz: list[float], num_samples: int, sample_rate_hz: float):
    chunk_size = 64
    preamble = []
    for _ in range(0, num_samples, chunk_size):
        chunk = inverse_fft([random.choice(frequencies_hz)], chunk_size, sample_rate_hz)
        preamble += chunk

    remainder = num_samples - len(preamble)
    preamble += inverse_fft(random.choice(frequencies_hz), remainder, sample_rate_hz)

    return preamble


def test_receiver():
    symbol_map = SymbolMap(default_symbol_size, default_symbol_weight)
    modulation = OFDM(
        default_symbol_weight,
        default_symbol_size,
        default_samples_per_symbol,
        default_sample_rate_hz,
        default_frequency_range_start_hz,
        default_frequency_range_end_hz
    )

    preamble = random_frequencies(modulation.frequencies_hz, 4096, modulation.sample_rate_hz)

    receiver = Receiver(modulation, preamble)

    text_over_sound = TextOverSound(default_samples_per_symbol,
                                    default_frequency_range_start_hz,
                                    default_frequency_range_end_hz,
                                    default_symbol_size,
                                    default_symbol_weight,
                                    default_sample_rate_hz)

    message_signal = pcm_to_signal(text_over_sound.string_to_pcm_data("Daniel"))

    noise_size = 5 * len(preamble)
    noise = [random.choice([-1, 1]) * random.random() for _ in range(noise_size)]

    final_test_signal = noise + preamble + message_signal

    for chunk_index in range(0, len(final_test_signal), default_samples_per_symbol):
        chunk = final_test_signal[chunk_index:chunk_index + default_samples_per_symbol]
        receiver.receive_buffer(chunk)

    message = symbol_map.symbols_to_string(receiver.get_message())
    print(message)


def main():
    test_receiver()


    initial_message = "ttst"
    text_over_sound = TextOverSound(4096,
                                    500,
                                    5_000,
                                    16,
                                    3,
                                    16_000)

    # pcm_data_initial_message = text_over_sound.string_to_pcm_data(initial_message)
    #
    # signal = text_over_sound.pcm_to_signal(pcm_data_initial_message)
    #
    # pcm_preamble = text_over_sound.string_to_pcm_data('s')
    # preamble = text_over_sound.pcm_to_signal(pcm_preamble)
    #
    # normalized_signal = (signal - np.mean(signal)) / (np.std(signal))
    # normalized_preamble = (preamble - np.mean(preamble)) / (np.std(preamble))
    #
    # correlation = np.correlate(normalized_signal,
    #                            normalized_preamble) / len(normalized_preamble)
    # peak_index = np.argmax(correlation)
    #
    # # Initializing the Library Object
    initial_message = "Error Correcting Codes"

    # Modulating the text to a PCM of an audio signal
    pcm_data_initial_message = text_over_sound.string_to_pcm_data(initial_message)

    recovered_message = text_over_sound.pcm_to_string(pcm_data_initial_message)
    print(f"Sent string: {initial_message}. recovered string: {recovered_message}")

    # instantiate PyAudio
    playback = pyaudio.PyAudio()

    # open stream
    stream = playback.open(format=playback.get_format_from_width(2),
                           channels=1,
                           rate=text_over_sound.sample_rate_hz,
                           output=True)

    # play stream
    stream.write(pcm_data_initial_message)

    # stop stream
    stream.stop_stream()
    stream.close()

    # close PyAudio
    playback.terminate()


if __name__ == '__main__':
    main()
