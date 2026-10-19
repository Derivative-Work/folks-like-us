# Timing map spot check [H]

Play the check video: the master, with each word shown large when the timing map says it starts, the whole line
below, and the timecode and frame number top left.

```
vlc renders/check/timing_check.mp4
```

The brief asks for five cues checked by ear; these are the ones the edit cuts on. Is each word's start within a frame
or two (≤ 80 ms) of when you hear it?

| Cue | Word | Start |
| --- | --- | --- |
| ST1 swerve | "—day." | 34.40 s (0:34.4) |
| ST2 swerve | "It's" | 55.67 s (0:55.7) |
| ST3 swerve | "—you!" | 85.41 s (1:25.4) |
| ST4 swerve | "It's" | 107.71 s (1:47.7) |
| Tag, start of F2 | "written" | 124.81 s (2:04.8) |

## Words to confirm

`lyrics/as_sung.txt` keeps the submitted wording here, but Whisper heard something different or nothing at all.
Is each one sung as written?

| Word | Start | Aligner score |
| --- | --- | --- |
| And out past (heard as "now past") | 23.84 s (0:23.8) | 0.76 |
| Gonna (chorus 1) | 41.39 s (0:41.4) | 0.72 |
| We (final chorus) | 88.69 s (1:28.7) | 0.99 |
| all (final chorus, "bet it all on") | 95.22 s (1:35.2) | 0.50 |

## Already established from the stems

- Chorus 1 sings "It's apple pie!" twice (55.67 s and 58.90 s).
- Suno dropped "sung by artificial intelligence" from the tag.
- The outro is instrumental (no vocals after 134.14 s).

## Result

2026-10-19, [H]: all five cues are good, and all four words are sung as written (`log/human_interventions.md`, entry 5).
`lyrics/as_sung.txt` and `timing/timing_map.json` stand as they are.
