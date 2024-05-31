import random
import threading
import time

import pyaudio
from text_over_sound import TextOverSound
from symbol_map import SymbolMap
from OFDM import OFDM
from receiver import Receiver
from utils import *
import numpy as np
import sounddevice as sd
import wave

default_samples_per_symbol = 4096
default_frequency_range_start_hz = 500
default_frequency_range_end_hz = 5_000
default_symbol_size = 16
default_symbol_weight = 3
default_sample_rate_hz = 16_000


def normalized_correlation(signal, preamble):
    normalized_signal = np.array(signal) / np.std(signal)
    normalized_preamble = np.array(preamble) / np.std(preamble)

    return np.correlate(normalized_signal, normalized_preamble, mode='valid') / min(len(signal), len(preamble))


def random_frequencies(frequencies_hz: list[float], num_samples: int, sample_rate_hz: float):
    chunk_size = 64
    preamble = []
    for freq_index, _ in enumerate(range(0, num_samples, chunk_size)):
        chunk = inverse_fft([random.choice(frequencies_hz)], chunk_size, sample_rate_hz)
        preamble += chunk

    remainder = num_samples - len(preamble)
    preamble += inverse_fft([random.choice(frequencies_hz)], remainder, sample_rate_hz)

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

    preamble = random_frequencies(
        modulation.frequencies_hz,
        4096,
        modulation.sample_rate_hz)

    receiver = Receiver(modulation, preamble)

    text_over_sound = TextOverSound(default_samples_per_symbol,
                                    default_frequency_range_start_hz,
                                    default_frequency_range_end_hz,
                                    default_symbol_size,
                                    default_symbol_weight,
                                    default_sample_rate_hz)

    message_signal = pcm_to_signal(text_over_sound.string_to_pcm_data("Moriya"))

    noise_size = int(2.7 * len(preamble))
    noise = [random.choice([-1, 1]) * random.random() for _ in range(noise_size)]

    final_test_signal = noise + preamble + message_signal

    for chunk_index in range(0, len(final_test_signal), default_samples_per_symbol):
        chunk = final_test_signal[chunk_index:chunk_index + default_samples_per_symbol]
        receiver.receive_buffer(chunk)

    message = symbol_map.symbols_to_string(receiver.get_message())
    print(message)


def load_audio_file(path: str) -> bytes:
    with wave.open(path, "rb") as audio_file:
        return audio_file.readframes(audio_file.getnframes())


def store_audio_file(path: str, pcm_data: bytes):
    with wave.open(path, "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(default_sample_rate_hz)
        audio_file.writeframesraw(pcm_data)


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
    recording_event = threading.Event()
    def signal_handler(input_data: bytes, frame_count: int, time_info, status: sd.CallbackFlags):
        nonlocal full_data
        nonlocal recording_event
        receiver.receive_buffer(pcm_to_signal(input_data))
        new_message = receiver.get_message()
        if len(new_message) != 0 and new_message[-1] == symbol_map.termination_symbol:
            recording_event.set()
            return None, pyaudio.paComplete
        print(symbol_map.symbols_to_string(new_message))
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
    timeout_sec = 10
    recording_event.wait()
    print("\nStopped recording!")

    recorder.terminate()
    message_signal = pcm_to_signal(full_data)
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

    test_signal = 3 * preamble + modulation.symbols_to_signal(symbol_map.string_to_symbols("Moriya is here")) + modulation.symbol_to_signal(symbol_map.termination_symbol)
    # store_audio_file("sample<N>.wav", signal_to_pcm(test_signal))

    receiver = Receiver(modulation, preamble)

    # test_receiver()
    # test_recorded_file(receiver, symbol_map, "test_out.wav")
    test_receiver_live(symbol_map, receiver)


if __name__ == '__main__':
    main()
