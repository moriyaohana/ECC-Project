import numpy as np
from scipy.ndimage.filters import uniform_filter1d
from matplotlib import pyplot as plt


def signal_to_pcm(signal: list[float]) -> bytes:
    # 32767 is the maximum value for 16-bit signed integer
    # sound is represented by a 16 bit value PCM16 (sound format)
    # Normalization by symbol_weight needed to prevent overflow
    PCM_16BIT_MAXIMUM_VALUE = 32767.0
    pcm_data = np.array([int(sample * PCM_16BIT_MAXIMUM_VALUE) for sample in signal], dtype=np.int16)

    return pcm_data.tobytes()

def pcm_to_signal(pcm_data: bytes) -> list[float]:
    pcm_array = np.frombuffer(pcm_data, dtype=np.int16)

    PCM_16BIT_MAXIMUM_VALUE = 32767.0
    return list(pcm_array / PCM_16BIT_MAXIMUM_VALUE)


def signal_fft(signal: list[float], sample_rate_hz: float) -> list[tuple[float, float]]:
    fft_magnitudes = np.fft.fft(signal)[:len(signal) // 2]
    sampled_frequencies = np.fft.fftfreq(len(signal), 1 / sample_rate_hz)[
                          :len(signal) // 2]

    assert (len(fft_magnitudes) == len(sampled_frequencies))

    return list(zip(sampled_frequencies, np.abs(fft_magnitudes)))


def plot_signal(signal: list[float], sample_rate_hz: float):
    t = np.linspace(0, len(signal) / sample_rate_hz, len(signal), endpoint=False)

    plt.plot(t, signal)
    plt.title('Original Signal')
    plt.xlabel('Time (sec)')
    plt.ylabel('Amplitude')

    plt.show()


def plot_signal_fft(signal: list[float], sample_rate_hz: float):
    f, fft = list(zip(*signal_fft(signal, sample_rate_hz)))
    plt.plot(f, fft)

    plt.title('FFT Result freq')
    plt.xlabel('frequency (Hz)')
    plt.ylabel('Amplitude')

    plt.show()


def inverse_fft(frequencies_hz: list[float], num_samples: int, sample_rate_hz: float) -> list[float]:
    sum_of_sin = []
    for time_step in range(num_samples):  # num_samples is representing discrete time axis t[s]

        sin_values = [np.sin(2 * np.pi * frequency * time_step / sample_rate_hz) for frequency in
                      frequencies_hz]

        sample = sum(sin_values) / len(sin_values)
        sum_of_sin.append(sample)

    return sum_of_sin


def vec_corrcoef(X, y, axis=1):
    Xm = np.mean(X, axis=axis, keepdims=True)
    ym = np.mean(y)
    n = np.sum((X - Xm) * (y - ym), axis=axis)
    d = np.sqrt(np.sum((X - Xm) ** 2, axis=axis) * np.sum((y - ym) ** 2))
    return n / d


def rolling_std(data: np.ndarray, window_size: int) -> np.ndarray:
    rolling_mean = uniform_filter1d(data,
                                    window_size,
                                    mode='constant',
                                    cval=0,
                                    origin=-window_size//2)
    rolling_mean_squares = uniform_filter1d(data*data,
                                            window_size,
                                            mode='constant',
                                            cval=0,
                                            origin=-window_size//2)
    return np.sqrt(rolling_mean_squares - rolling_mean*rolling_mean)[:-window_size + 1]
