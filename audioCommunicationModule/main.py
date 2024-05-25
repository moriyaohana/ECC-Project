import random
import time

import pyaudio
from text_over_sound import TextOverSound
from symbol_map import SymbolMap
from OFDM import OFDM
from receiver import Receiver
from utils import *
import numpy as np
import sounddevice as sd

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

        start_time = time.time()
        receiver.receive_buffer(audio_signal[chunk_index:chunk_index + chunk_size])
        end_time = time.time()
        print(
            f"receive took {end_time - start_time} seconds. "
            f"block duration is {default_samples_per_symbol / default_samples_per_symbol} seconds")

    message = symbol_map.symbols_to_string(receiver.get_message())
    print(message)


def test_receiver_live(symbol_map: SymbolMap, receiver: Receiver):
    full_data = bytes()
    message = list()
    # noinspection PyUnusedLocal
    def signal_handler(input_data: bytes, frame_count: int, time_info, status: sd.CallbackFlags):
        nonlocal full_data
        nonlocal message
        receiver.receive_buffer(pcm_to_signal(input_data))
        new_message = receiver.get_message()
        if len(new_message) > len(message):
            if new_message[-1] == symbol_map.termination_symbol:
                return None, pyaudio.paAbort
            print(symbol_map.symbols_to_string(new_message[len(message):]), end='')
            message = new_message
        full_data += input_data

        return None, pyaudio.paContinue

    recorder = pyaudio.PyAudio()

    # noinspection PyTypeChecker
    recorder.open(format=recorder.get_format_from_width(2),
                  channels=1,
                  rate=int(default_sample_rate_hz),
                  input=True,
                  frames_per_buffer=default_samples_per_symbol,
                  stream_callback=signal_handler)

    print("Recording...")
    sd.sleep(10000)
    print("\nStopped recording!")

    recorder.terminate()
    print(symbol_map.symbols_to_string(receiver.get_message()))


def play_pcm(pcm: bytes, sample_rate_hz: float):
    # instantiate PyAudio
    playback = pyaudio.PyAudio()

    # open stream
    stream = playback.open(format=playback.get_format_from_width(2),
                           channels=1,
                           rate=int(sample_rate_hz),
                           output=True)

    # play stream
    stream.write(pcm)

    # stop stream
    stream.stop_stream()
    stream.close()

    # close PyAudio
    playback.terminate()


def play_test_data(text_over_sound: TextOverSound, message: str, preamble: list[float]):
    pcm_data = signal_to_pcm(preamble) + text_over_sound.string_to_pcm_data(message)
    play_pcm(pcm_data, default_sample_rate_hz)


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

    # noinspection PyUnusedLocal
    text_over_sound = TextOverSound(default_samples_per_symbol,
                                    default_frequency_range_start_hz,
                                    default_frequency_range_end_hz,
                                    default_symbol_size,
                                    default_symbol_weight,
                                    default_sample_rate_hz)

    # preamble = random_frequencies(modulation.frequencies_hz, 4096, modulation.sample_rate_hz)
    preamble = modulation.symbol_to_signal(symbol_map.sync_symbol)

    receiver = Receiver(modulation, preamble)

    # test_receiver_live(symbol_map, receiver)
    test_recorded_file(receiver, symbol_map, "test_out.wav")


if __name__ == '__main__':
    main()
