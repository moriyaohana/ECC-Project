import random
import threading
import time

import pyaudio
from symbol_map import SymbolMap
from OFDM import OFDM
from receiver import Receiver
from utils import *
import numpy as np
import sounddevice as sd
import wave
import reedsolo

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

    chunk_size = receiver._modulation.samples_per_symbol
    for chunk_index in range(0, len(audio_signal), chunk_size):
        if receiver._is_synced:
            print(symbol_map.symbols_to_string(receiver.get_message_symbols()))

        start_time = time.time()
        receiver.receive_buffer(audio_signal[chunk_index:chunk_index + chunk_size])
        end_time = time.time()
        print(
            f"receive took {end_time - start_time} seconds. "
            f"block duration is {default_samples_per_symbol / default_samples_per_symbol} seconds")

    message = symbol_map.symbols_to_string(receiver.get_message_symbols())
    print(message)


def decode_string(data: bytes, erasures: set[int], default_char: str = "_", should_correct=False):
    decoded_data = data.decode("utf-8", errors="replace")
    org = "".join(default_char if index in erasures else char for index, char in enumerate(decoded_data))
    if not should_correct:
        return org
    rscode = reedsolo.RSCodec(10)

    try:
        corrected_message, _, errata = rscode.decode(data, erase_pos=erasures)
    except ...:
        print("No errors corrected! Either too many errors, or no errors at all")
        corrected_message = org
    print(f"org: {org}")
    print(f"cor: {corrected_message}")
    return corrected_message.decode("utf-8", errors="replace")


def encode_string(string: str):
    byte_data = string.encode("utf-8")
    rscode = reedsolo.RSCodec(10)
    return rscode.encode(byte_data)


def test_receiver_live(symbol_map: SymbolMap, receiver: Receiver):
    full_data = bytes()
    recording_event = threading.Event()

    def signal_handler(input_data: bytes, frame_count: int, time_info, status: sd.CallbackFlags):
        start_time = time.time()
        nonlocal full_data
        nonlocal recording_event
        receiver.receive_buffer(pcm_to_signal(input_data))
        new_message_symbols = receiver.get_message_symbols()
        end_time = time.time()
        # print(f"took {end_time - start_time} secs")
        if len(new_message_symbols) != 0 and new_message_symbols[-1] == symbol_map.termination_symbol:
            recording_event.set()
            return None, pyaudio.paComplete
        print(decode_string(*receiver.get_message_data()))
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
    timeout_sec = 15
    recording_event.wait(timeout_sec)
    print("\nStopped recording!")

    recorder.terminate()
    message_signal = np.array(pcm_to_signal(full_data))
    data, erasures = receiver.get_message_data()
    print(f"final message: {decode_string(data, erasures, should_correct=True)} with {len(erasures)} erasures")


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


def main():
    symbol_map = SymbolMap(default_symbol_size, default_symbol_weight)

    receiver = Receiver(default_symbol_weight,
                        default_symbol_size,
                        default_samples_per_symbol,
                        default_sample_rate_hz,
                        default_frequency_range_start_hz,
                        default_frequency_range_end_hz,
                        snr_threshold=2)

    message = "Moriya is here"
    encoded_message = encode_string(message)
    print(f"Transmitting: {encoded_message}")
    test_signal = 3 * receiver.sync_preamble + receiver._modulation.data_to_signal(
        encoded_message) + receiver._modulation.symbols_to_signal(
        symbol_map.termination_symbol)
    # store_audio_file("sample10.wav", signal_to_pcm(test_signal))

    # test_recorded_file(receiver, symbol_map, "test_out.wav")
    test_receiver_live(symbol_map, receiver)


if __name__ == '__main__':
    main()
