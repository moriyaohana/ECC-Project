from matplotlib import pyplot as plt
from utils import *


def plot_signal(signal: List[float], sample_rate_hz: float):
    t = np.linspace(0, len(signal) / sample_rate_hz, len(signal), endpoint=False)

    plt.plot(t, signal)
    plt.title('Original Signal')
    plt.xlabel('Time (sec)')
    plt.ylabel('Amplitude')

    plt.show()


def plot_signal_fft(signal: List[float], sample_rate_hz: float):
    f, fft = list(zip(*signal_fft(signal, sample_rate_hz)))
    plt.plot(f, fft)

    plt.title('FFT Result freq')
    plt.xlabel('frequency (Hz)')
    plt.ylabel('Amplitude')

    plt.show()
