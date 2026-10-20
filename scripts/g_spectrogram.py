"""S34 (G plot): the mastering model's real failures, plotted from the archived files.

Top: a spectrogram of the mastered track (audio/master/folks_like_us_master_nofallback.wav), with F1-F3 from
timing/failure_map.json outlined and labelled. Bottom, on the same time axis: the failing change itself, the
no-fallback master minus the with-fallback master (the model's output where it failed), as short-term level in dB.
Outside F1-F3 the two masters are identical, so the line sits on the floor.

The frame is 1920x1080 on the dark chart surface; O lays the S34 card text over it. Colors (dataviz reference
palette, dark mode): magnitude on the one-hue blue ramp, quiet = surface; F regions in categorical slot 2 (orange)
outlines, labels in text ink.

Usage: .venv/bin/python scripts/g_spectrogram.py [out=takes/g/S34/S34_spectrogram.png]
"""
import json
import sys
from pathlib import Path

import librosa
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "takes/g/S34/S34_spectrogram.png")
NOFALLBACK = "audio/master/folks_like_us_master_nofallback.wav"
WITHFALLBACK = "audio/master/with-fallback/folks_like_us_master_withfallback.wav"
FMAP = json.load(open("timing/failure_map.json"))["regions"]

SURFACE, TEXT, TEXT_2, GRID = "#1a1a19", "#f0efec", "#c3c2b7", "#3a3a37"
F_COLOR = "#d95926"  # categorical slot 2, dark
RAMP = LinearSegmentedColormap.from_list(
    "blue", [SURFACE, "#104281", "#1c5cab", "#2a78d6", "#5598e7", "#86b6ef", "#cde2fb"])


def main():
    y, sr = librosa.load(NOFALLBACK, sr=None, mono=True)
    yf, _ = librosa.load(WITHFALLBACK, sr=sr, mono=True)
    n = min(len(y), len(yf))
    y, yf = y[:n], yf[:n]
    dur = n / sr

    hop = 512
    S = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=4096, hop_length=hop)), ref=np.max)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=4096)

    diff = y - yf
    win = int(0.05 * sr)
    rms = lambda x: np.sqrt(np.convolve(x ** 2, np.ones(win) / win, mode="same"))  # noqa: E731
    step = win // 4
    t = np.arange(0, n, step) / sr
    level = 20 * np.log10(np.maximum(rms(diff)[::step], 1e-6))
    master = 20 * np.log10(np.maximum(rms(y)[::step], 1e-6))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15, "text.color": TEXT,
                         "axes.labelcolor": TEXT_2, "xtick.color": TEXT_2, "ytick.color": TEXT_2})
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=SURFACE)
    top = fig.add_axes([0.07, 0.40, 0.88, 0.47], facecolor=SURFACE)
    bot = fig.add_axes([0.07, 0.12, 0.88, 0.21], facecolor=SURFACE, sharex=top)

    top.imshow(S, origin="lower", aspect="auto", cmap=RAMP, vmin=-80, vmax=0, interpolation="bilinear",
               extent=[0, dur, freqs[0] / 1000, freqs[-1] / 1000])
    top.set_ylim(0, 16)
    top.set_ylabel("Frequency (kHz)")
    plt.setp(top.get_xticklabels(), visible=False)

    bot.plot(t, master, color=TEXT_2, linewidth=1, alpha=0.5)
    bot.plot(t, level, color=F_COLOR, linewidth=2)
    bot.set_ylim(-100, 0)
    bot.set_ylabel("Level (dB)")
    bot.set_xlabel("Time (s)")
    bot.set_xlim(0, dur)
    bot.grid(axis="y", color=GRID, linewidth=0.8)
    bot.text(2, -12, "the song", color=TEXT_2, fontsize=14, va="center")
    bot.text(2, -88, "the model's failing change (no-fallback minus with-fallback)", color=TEXT, fontsize=14,
             va="center")

    for name, r in FMAP.items():
        a, b = r["start"], r["end"]
        top.add_patch(Rectangle((a, 0.15), b - a, 15.7, fill=False, edgecolor=F_COLOR, linewidth=2.5))
        top.text((a + b) / 2, 16.4, name, color=TEXT, fontsize=20, fontweight="bold", ha="center", va="bottom",
                 clip_on=False)
        bot.axvspan(a, b, color=F_COLOR, alpha=0.12, linewidth=0)

    for ax in (top, bot):
        for s in ax.spines.values():
            s.set_color(GRID)
        ax.tick_params(length=0, pad=8)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor=SURFACE)
    print(OUT)


if __name__ == "__main__":
    main()
