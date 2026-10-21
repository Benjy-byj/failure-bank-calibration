# Overview video

The 4-minute narrated explainer of both workshop papers (1080p60, English narration with a soft
music bed, English subtitles as a selectable track) is published as `docs/talk.mp4` on the
[project page](https://benjy-byj.github.io/failure-bank-calibration/); its subtitles are in
`overview.srt` here and `docs/talk.vtt`. `overview_teaser.gif` is a silent excerpt for the repository front page.

Every number shown or spoken comes from the papers or from this repository; the per-loop
discoveries in the closed-loop scene are read from `sysloop/results/` (`replicates.json`).

## Rebuilding

The video is generated from code:

| File | Role |
|---|---|
| `narration.py` | narration script; synthesizes each sentence with Kokoro (voice `af_heart`) and writes `timeline.json` |
| `explainer.py` | the nine animated scenes (Manim Community); every animation is timed to its sentence in `timeline.json` |
| `assemble.py` | joins the scenes, generates the music bed and sound effects, ducks the music under the voice, normalizes to -16 LUFS, writes subtitles, muxes the MP4 |

Run these from inside `media/`:

```bash
pip install manim kokoro-onnx soundfile scipy        # also needs ffmpeg, Pango, and the Inter / JetBrains Mono fonts
mkdir -p models && cd models
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
cd ..
python3 narration.py                                  # -> audio/*.wav, timeline.json
for s in S1Title S2Bank S3Noise S4Asym S5Measured S6LLM S7Fix S8Result S9End; do
  manim -qh --disable_caching -o $s explainer.py $s
done
python3 assemble.py overview.mp4                    # then copy to ../docs/talk.mp4
```

The music and sound effects are synthesized in `assemble.py`; no third-party audio is used.
Fonts: [Inter](https://github.com/rsms/inter) and [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) (both SIL OFL).
