from matplotlib import pyplot as plt
from utils import *

plt.figure(figsize=(50, 10))

title_font = {
    "weight": "bold",
    "size": 22
}

label_font = {
    "weight": "normal",
    "size": 18
}

def plot_signal(signal: List[float], sample_rate_hz: float, title: str = 'Signal'):
    t = np.linspace(0, len(signal) / sample_rate_hz, len(signal), endpoint=False)
    plt.figure(figsize=(40, 10))
    plt.plot(t, signal)
    plt.title(title, fontdict=title_font)
    plt.xlabel('Time (sec)', fontdict=label_font)
    plt.ylabel('Amplitude', fontdict=label_font)

    plt.show()


def plot_signal_fft(signal: List[float], sample_rate_hz: float, title: str):
    f, fft = list(zip(*signal_fft(signal, sample_rate_hz)))
    plt.figure(figsize=(15, 10))
    plt.plot(f, fft)

    plt.title(title, fontdict=title_font)
    plt.xlabel('frequency (Hz)', fontdict=label_font)
    plt.ylabel('Amplitude', fontdict=label_font)

    plt.show()
