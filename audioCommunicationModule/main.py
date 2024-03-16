import pyaudio
from matplotlib import pyplot as plt
from text_over_sound import TextOverSound
import numpy as np


def main():
    initial_message = "s"
    text_over_sound = TextOverSound(4096,0.5, 2, 16, 3, 16)
    pcm_data_initial_message = text_over_sound.char_to_pcm_data(initial_message)

    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    text_over_sound.plot_signal_per_char(initial_message)

    plt.subplot(2, 1, 2)
    text_over_sound.plot_pcm_fft(pcm_data_initial_message)

    plt.tight_layout()
    plt.show()

    recovered_char = text_over_sound.pcm_to_char(pcm_data_initial_message)
    print(f"Sent char: {initial_message}. recovered_char: {recovered_char}")

    # instantiate PyAudio (1)
    p = pyaudio.PyAudio()

    KHZ_TO_HZ_FACTOR = 1000
    # open stream (2), 2 is size in bytes of int16
    stream = p.open(format=p.get_format_from_width(2),
                    channels=1,
                    rate=text_over_sound.sample_rate_khz * KHZ_TO_HZ_FACTOR,
                    output=True)

    # play stream (3), blocking call
    stream.write(pcm_data_initial_message)

    # stop stream (4)
    stream.stop_stream()
    stream.close()

    # close PyAudio (5)
    p.terminate()


if __name__ == '__main__':
    main()
