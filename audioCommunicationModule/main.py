import pyaudio

from text_over_sound import TextOverSound


def main():
    initial_message = "sofi and Moriya"
    text_over_sound = TextOverSound(250,10,20,16,3,16)
    pcm_data_initial_message = text_over_sound.string_to_pcm_data(initial_message)

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
