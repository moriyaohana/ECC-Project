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
    for freq_index, _ in enumerate(range(0, num_samples, chunk_size)):
        chunk = inverse_fft([frequencies_hz[(3 * freq_index) % len(frequencies_hz)]], chunk_size, sample_rate_hz)
        preamble += chunk

    remainder = num_samples - len(preamble)
    preamble += inverse_fft([frequencies_hz[-1]], remainder, sample_rate_hz)

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

    noise_size = int(2.7 * len(preamble))
    noise = [random.choice([-1, 1]) * random.random() for _ in range(noise_size)]

    final_test_signal = noise + preamble + message_signal

    for chunk_index in range(0, len(final_test_signal), default_samples_per_symbol):
        chunk = final_test_signal[chunk_index:chunk_index + default_samples_per_symbol]
        receiver.receive_buffer(chunk)

    message = symbol_map.symbols_to_string(receiver.get_message())
    print(message)


def load_audio_file(path: str) -> bytes:
    with open(path, "rb") as audio_file:
        return audio_file.read()


def test_recorded_file(receiver: Receiver, symbol_map: SymbolMap, path: str):
    audio_data = load_audio_file(path)
    audio_signal = pcm_to_signal(audio_data)

    chunk_size = receiver._modulation.num_samples
    for chunk_index in range(0, len(audio_signal), chunk_size):
        if receiver._is_synced:
            print(symbol_map.symbols_to_string(receiver.get_message()))
        receiver.receive_buffer(audio_signal[chunk_index:chunk_index + chunk_size])

    message = symbol_map.symbols_to_string(receiver.get_message())
    print(message)

def test_receiver_live(symbol_map: SymbolMap, receiver: Receiver, text_over_sound: TextOverSound):
    return

def play_test_data(text_over_sound: TextOverSound, message: str, preamble: list[float]):
    pcm_data = signal_to_pcm(preamble) + text_over_sound.string_to_pcm_data(message)
    # instantiate PyAudio
    playback = pyaudio.PyAudio()

    # open stream
    stream = playback.open(format=playback.get_format_from_width(2),
                           channels=1,
                           rate=text_over_sound.sample_rate_hz,
                           output=True)

    # play stream
    stream.write(pcm_data)

    # stop stream
    stream.stop_stream()
    stream.close()

    # close PyAudio
    playback.terminate()


def main():
    symbol_map = SymbolMap(default_symbol_size, default_symbol_weight)
    modulation = OFDM(
        default_symbol_weight,
        default_symbol_size,
        default_samples_per_symbol,
        default_sample_rate_hz,
        default_frequency_range_start_hz,
        default_frequency_range_end_hz
    )

    text_over_sound = TextOverSound(default_samples_per_symbol,
                                    default_frequency_range_start_hz,
                                    default_frequency_range_end_hz,
                                    default_symbol_size,
                                    default_symbol_weight,
                                    default_sample_rate_hz)

    preamble = random_frequencies(modulation.frequencies_hz, 4096, modulation.sample_rate_hz)

    receiver = Receiver(modulation, preamble)

    test_recorded_file(receiver, symbol_map, "message_example.wav")


if __name__ == '__main__':
    main()
