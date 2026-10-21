# music-deslop M6f 10k: with and without the fallback

Release chain (`postfilter.infer` defaults: M6f 10k, temperature 0, 18 kHz input lowpass, de-pump with 1.5 dB cut cap,
gain smoothing) on the author's own Suno songs, 24-bit 48 kHz WAV. This copy keeps Folks Like Us only.

- `with-fallback/`: the default. Where the raw model output turns noisy (median per-bin gain jitter in 2 s windows
  rising from 0.25 to 0.4 dB; normal music is about 0.09), the change fades out over 0.5 s and the input passes
  through.
- `no-fallback/`: the same chain with `--no-fallback`: the model's output everywhere.

Files are scaled down only if they would clip (to -0.1 dBFS); folks-like-us needed no scaling.

## Where the fallback was active

| song | length | passages | share faded |
|---|---|---|---|
| folks-like-us | 2:21.2 | 1:43.4–1:46.1 (97% of the change), 2:04.9–2:10.8 (input only), 2:13.7–2:21.1 (input only) | 11.3% |

Each passage lists the deepest fade inside it: "input only" means the model's change was fully removed there.
