import random
import threading
import time

import pyaudio
from symbol_map import SymbolMap
from receiver import Receiver
from transmitter import Transmitter
from utils import *
import numpy as np
import sounddevice as sd
import wave
import reedsolo


default_samples_per_symbol = 4096
default_frequency_range_start_hz = 2_000
default_frequency_range_end_hz = 4_000
default_symbol_size = 16
default_symbol_weight = 3
default_sample_rate_hz = 16_000
default_nsym = 5
default_nsize = 15


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
    audio_signal = [0] * 2048 + pcm_to_signal(audio_data)

    chunk_size = default_samples_per_symbol
    for chunk_index in range(0, len(audio_signal), chunk_size):
        receiver.receive_buffer(audio_signal[chunk_index:chunk_index + chunk_size])

    message_history = receiver.message_history
    print(message_history)


def test_receiver_live(receiver: Receiver):
    full_data = bytes()
    recording_event = threading.Event()
    received_message = []

    def signal_handler(input_data: bytes, frame_count: int, time_info, status: sd.CallbackFlags):
        start_time = time.time()
        nonlocal full_data
        nonlocal recording_event
        receiver.receive_buffer(pcm_to_signal(input_data))

        # if receiver.last_symbol is not None:
        #     print(symbol_map.symbols_to_bytes([receiver.last_symbol])[0].decode('ascii', errors='ignore'), end='')
        # end_time = time.time()
        # print(f"took {end_time - start_time} secs")
        # if receiver.last_symbol == symbol_map.termination_symbol:
        #     recording_event.set()
        #     return None, pyaudio.paComplete
        # print(decode_string(*symbol_map.symbols_to_bytes(new_message_symbols)))
        full_data += input_data

        if len(receiver.message_history) > 0:
            recording_event.set()
            return None, pyaudio.paComplete

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
    timeout_sec = 7
    recording_event.wait(timeout_sec)
    print("\nStopped recording!")

    recorder.terminate()
    message_signal = np.array(pcm_to_signal(full_data))
    data = receiver.message_history
    print(f"final message: '{data[0][2]}'")
    return


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


def transmitter_demonstration(transmitter: Transmitter):
    while True:
        message = input("Enter Message: ")
        message_signal = transmitter.transmit_buffer(message.encode('ascii'))
        play_pcm(signal_to_pcm(message_signal), default_sample_rate_hz)


def main():
    symbol_map = SymbolMap(default_symbol_size, default_symbol_weight)
    ecc_codec = reedsolo.RSCodec(default_nsym, default_nsize)
    receiver = Receiver(default_symbol_weight,
                        default_symbol_size,
                        default_samples_per_symbol,
                        default_sample_rate_hz,
                        default_frequency_range_start_hz,
                        default_frequency_range_end_hz,
                        default_nsym,
                        default_nsize,
                        snr_threshold=1.5,
                        correlation_threshold=0.4)

    transmitter = Transmitter(default_symbol_weight,
                              default_symbol_size,
                              default_samples_per_symbol,
                              default_sample_rate_hz,
                              default_frequency_range_start_hz,
                              default_frequency_range_end_hz,
                              2, # default_nysym,
                              default_nsize,
                              snr_threshold=1.5)

    message = "To go"
    print(transmitter._ecc_codec.encode(message.encode('ascii')))
    message_signal = transmitter.transmit_buffer(message.encode('ascii'))
    # play_pcm(signal_to_pcm(message_signal), 16000)
    # store_audio_file("samples\\sample24.wav", signal_to_pcm(message_signal))

    transmitter_demonstration(transmitter)

    # test_recorded_file(receiver, symbol_map, "samples/sample24.wav")
    # test_receiver_live(receiver)


if __name__ == '__main__':
    main()
