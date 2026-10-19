# music-deslop M6f 10k: with and without the fallback

Release chain (`postfilter.infer` defaults: M6f 10k, temperature 0, 18 kHz input lowpass, de-pump with 1.5 dB cut cap,
gain smoothing) on the author's own Suno songs, 24-bit 48 kHz WAV.

- `with-fallback/`: the default. Where the raw model output turns noisy (median per-bin gain jitter in 2 s windows
  rising from 0.25 to 0.4 dB; normal music is about 0.09), the change fades out over 0.5 s and the input passes
  through.
- `no-fallback/`: the same chain with `--no-fallback`: the model's output everywhere.

Files are scaled down only if they would clip (to -0.1 dBFS): ghost-in-the-machine -0.13 dB, sandbox-rhapsody -0.27 dB,
sanding-the-truth -0.29 dB, the same in both folders. Songs with no fallback passages are the same in both folders (to within one 24-bit step on a few samples, from rounding).

## Where the fallback was active

| song | length | passages | share faded |
|---|---|---|---|
| field-of-humming-things | 3:58.4 | 1:12.4–1:22.6 (input only), 3:11.2–3:48.9 (input only) | 20.1% |
| folks-like-us | 2:21.2 | 1:43.4–1:46.1 (97% of the change), 2:04.9–2:10.8 (input only), 2:13.7–2:21.1 (input only) | 11.3% |
| ghost-in-the-machine | 3:10.0 | none | 0.0% |
| grading-ghosts | 3:16.4 | none | 0.0% |
| read-only | 3:16.2 | none | 0.0% |
| nobody-wrote-this-song | 2:36.0 | none | 0.0% |
| sandbox-rhapsody | 5:23.0 | none | 0.0% |
| sanding-the-truth | 4:52.6 | none | 0.0% |

Each passage lists the deepest fade inside it: "input only" means the model's change was fully removed there.
field-of-humming-things 3:11–3:49 is the very wide stereo ending that produced the "digital noise" artifact.
