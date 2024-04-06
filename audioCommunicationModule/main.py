import pyaudio
from text_over_sound import TextOverSound


def main():
    # Initializing the Library Object
    text_over_sound = TextOverSound(4096,
                                    0.5,
                                    5,
                                    16,
                                    3,
                                    16)

    initial_message = "Error Correcting Codes"

    # Modulating the text to a PCM of an audio signal
    pcm_data_initial_message = text_over_sound.string_to_pcm_data(initial_message)

    recovered_message = text_over_sound.pcm_to_string(pcm_data_initial_message)
    print(f"Sent string: {initial_message}. recovered string: {recovered_message}")

    # instantiate PyAudio
    playback = pyaudio.PyAudio()

    KHZ_TO_HZ_FACTOR = 1000
    # open stream
    stream = playback.open(format=playback.get_format_from_width(2),
                           channels=1,
                           rate=text_over_sound.sample_rate_khz * KHZ_TO_HZ_FACTOR,
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
