"""Assemble the overview video: concatenate rendered scenes, build the soundtrack
(narration + generated music bed with ducking + a few sound effects), loudness-normalize,
write subtitles, and mux everything into one MP4.
Usage: python3 assemble.py OUT.mp4 [--quality 1080p60] [--no-music]"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly

HERE = Path(__file__).resolve().parent
SR = 48000
SCENES = ["S1Title", "S2Bank", "S3Noise", "S4Asym", "S5Measured", "S6LLM", "S7Fix", "S8Result", "S9End"]
KEYS = ["title", "bank", "noise", "asym", "measured", "llm", "fix", "result", "end"]


def run(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


# ------------------------------------------------------------------ music
def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def music_bed(total, rng):
    """Slow D-major pad (Dmaj7 - Bm7 - Gmaj7 - A) with a soft bass and a sparse pluck arpeggio."""
    t = np.arange(int(total * SR)) / SR
    L = np.zeros_like(t); R = np.zeros_like(t)
    chords = [[50, 57, 62, 66, 69, 73], [47, 54, 62, 66, 69, 74], [43, 55, 62, 66, 71, 74], [45, 52, 61, 64, 69, 71]]
    seg = 8.0
    n_seg = int(np.ceil(total / seg)) + 1
    for i in range(n_seg):
        ch = chords[i % 4]
        t0 = i * seg - 1.5
        a, b = max(0, int(t0 * SR)), min(len(t), int((t0 + seg + 3.0) * SR))
        if a >= b:
            continue
        tt = t[a:b] - t0
        env = np.clip(tt / 2.5, 0, 1) * np.clip((seg + 3.0 - tt) / 2.5, 0, 1)
        env = env ** 2 * (3 - 2 * env)                                   # smoothstep crossfade
        for j, n in enumerate(ch):
            f = midi(n)
            amp = (0.9 if j == 0 else 0.55) / len(ch)
            for det, side in ((-0.004, 0), (0.0, 2), (0.004, 1)):          # three detuned voices, spread L/C/R
                ph = rng.uniform(0, 2 * np.pi)
                w = 2 * np.pi * f * (1 + det) * tt + ph
                s = np.sin(w) + 0.22 * np.sin(2 * w) + 0.06 * np.sin(3 * w)
                s *= amp * env * (1 + 0.15 * np.sin(2 * np.pi * 0.07 * tt + ph))
                if side == 0: L[a:b] += s
                elif side == 1: R[a:b] += s
                else: L[a:b] += 0.7 * s; R[a:b] += 0.7 * s
        bass = 0.32 * np.sin(2 * np.pi * midi(ch[0] - 12) * tt) * env      # soft bass an octave below
        L[a:b] += bass; R[a:b] += bass
    # pluck arpeggio, quarter notes at 70 bpm, starting after the title
    beat = 60 / 70
    pat = [0, 2, 3, 4, 3, 2, 1, 2]
    k = 0
    tb = 9.5
    while tb < total - 6:
        ch = chords[int(tb // seg) % 4]
        if rng.random() > 0.18:
            n = ch[pat[k % len(pat)]] + 12
            a = int(tb * SR); b = min(len(t), a + int(1.6 * SR))
            tt = t[a:b] - tb
            w = 2 * np.pi * midi(n) * tt
            s = (np.sin(w) + 0.25 * np.sin(2 * w)) * np.exp(-tt / 0.45) * (1 - np.exp(-tt / 0.004)) * 0.10
            pan = 0.5 + 0.35 * np.sin(k * 0.9)
            L[a:b] += s * (1 - pan) * 1.4; R[a:b] += s * pan * 1.4
        k += 1; tb += beat
    sos = butter(2, 2600, "low", fs=SR, output="sos")
    L, R = sosfilt(sos, L), sosfilt(sos, R)
    # simple stereo reverb: exponentially decaying noise impulse responses
    n_ir = int(2.4 * SR)
    ti = np.arange(n_ir) / SR
    irL = rng.standard_normal(n_ir) * np.exp(-ti / 0.55); irR = rng.standard_normal(n_ir) * np.exp(-ti / 0.55)
    irL /= np.sqrt(np.sum(irL ** 2)); irR /= np.sqrt(np.sum(irR ** 2))
    L = 0.75 * L + 0.45 * fftconvolve(L, irL)[:len(L)]
    R = 0.75 * R + 0.45 * fftconvolve(R, irR)[:len(R)]
    fade = np.clip(t / 2.5, 0, 1) * np.clip((total - t) / 4.0, 0, 1)
    return np.stack([L * fade, R * fade], 1)


# ------------------------------------------------------------------ sfx
def sfx(name, rng):
    n = int(1.6 * SR); t = np.arange(n) / SR
    if name == "thud":
        f = 55 + 70 * np.exp(-t / 0.025)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)
        nz = sosfilt(butter(2, 1800, "low", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-t / 0.012) * 0.6
        s = 0.55 * (s + nz)
    elif name == "tick":
        s = (np.sin(2 * np.pi * 1500 * t) + 0.3 * np.sin(2 * np.pi * 3000 * t)) * np.exp(-t / 0.018) * 0.10
    elif name == "chime":
        s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in ((1174.7, 1.0, 0.7), (1760.0, 0.6, 0.5), (2349.3, 0.2, 0.3)))
        s *= (1 - np.exp(-t / 0.003)) * 0.09
    elif name == "lock":
        def click(at, g):
            c = np.zeros(n); i = int(at * SR); m = int(0.012 * SR)
            c[i:i + m] = rng.standard_normal(m) * np.exp(-np.arange(m) / (0.002 * SR)) * g
            return c
        s = sosfilt(butter(2, [900, 4000], "band", fs=SR, output="sos"), click(0, 1.0) + click(0.065, 0.7))
        s = s * 0.5 + 0.25 * np.sin(2 * np.pi * 90 * t) * np.exp(-t / 0.06)
    else:
        raise ValueError(name)
    return s


# ------------------------------------------------------------------ subtitles
def fmt_ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def cues_for(text, start, dur, max_chars=90):
    sents = re.split(r"(?<=[.?!:;])\s+", text.strip())
    chunks, cur = [], ""
    for s_ in sents:
        if cur and len(cur) + len(s_) + 1 > max_chars:
            chunks.append(cur); cur = s_
        else:
            cur = (cur + " " + s_).strip()
    chunks.append(cur)
    tot = sum(len(c) for c in chunks)
    out, t = [], start
    for c in chunks:
        d = dur * len(c) / tot
        out.append((t, t + d, c)); t += d
    return out


def display_text(s):
    """Narration is written for the voice; subtitles use the written forms."""
    rep = {"F C Net": "FCNet", "zero point seven nine": "0.79", "zero point nine six": "0.96", "seventeen and a half percent": "17.5%",
           "nineteen percent": "19%", "a hundred and twenty-two thousand": "122,817", "thirty-two and a half percent": "32.5%",
           "eight and a half": "8.5%", "twelve": "12", "nine families": "9 families", "ninety-four": "94",
           "sixty point five": "60.5", "thirty to thirty-two percent": "30–32%", "thirteen point nine": "13.9",
           "ninety-five percent": "95%", "nine point seven": "9.7", "eighteen point one": "18.1", "forty-six": "46",
           "eight independent loops": "8 independent loops", "A.I.": "AI"}
    for a, b in rep.items():
        s = s.replace(a, b)
    return s


# ------------------------------------------------------------------ main
def main():
    out = Path(sys.argv[1]).resolve()
    q = sys.argv[sys.argv.index("--quality") + 1] if "--quality" in sys.argv else "1080p60"
    use_music = "--no-music" not in sys.argv
    work = HERE / "build"; work.mkdir(exist_ok=True)
    tl = json.load(open(HERE / "timeline.json"))
    vids = [HERE / f"media/videos/explainer/{q}/{s}.mp4" for s in SCENES]
    durs = [duration(v) for v in vids]
    offs = np.concatenate([[0], np.cumsum(durs)[:-1]])
    total = float(sum(durs))
    print("scenes:", " ".join(f"{d:.2f}" for d in durs), "total", round(total, 2))

    # video: concatenate and re-encode once with colour tags
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{v}'\n" for v in vids))
    vid = work / "video.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-tune", "animation",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-an", str(vid)])

    # audio
    rng = np.random.default_rng(11)
    n = int(np.ceil(total * SR)) + SR
    voice = np.zeros(n); mask = np.zeros(n)
    cues = []
    for key, off in zip(KEYS, offs):
        for b in tl[key]["beats"]:
            s, sr = sf.read(HERE / b["wav"])
            if s.ndim > 1: s = s.mean(1)
            s = resample_poly(s, SR, sr) if sr != SR else s
            a = int((off + b["start"]) * SR)
            voice[a:a + len(s)] += s
            mask[a:a + len(s)] = 1
            cues += cues_for(display_text(b["text"]), off + b["start"], b["dur"])
    fx = np.zeros(n)
    for key, off in zip(KEYS, offs):
        p = HERE / f"sfx_{key}.json"
        for t_, name in (json.load(open(p)) if p.exists() else []):
            s = sfx(name, rng); a = int((off + t_) * SR); fx[a:a + len(s)] += s[: max(0, n - a)]
    mix = np.stack([voice, voice], 1) * 1.0 + np.stack([fx, fx], 1)
    if use_music:
        bed = music_bed(n / SR, rng)
        # ducking: -7 dB under narration with 0.3 s attack / 0.8 s release
        hop = SR // 100
        m = mask[::hop]
        env = np.empty_like(m); g = 0.0
        for i, v in enumerate(m):
            g += (v - g) * (0.033 if v > g else 0.0125)
            env[i] = g
        env = np.repeat(env, hop)[:n]
        duck = 1 - (1 - 10 ** (-7 / 20)) * env
        bed_rms = np.sqrt(np.mean(bed ** 2)); voice_rms = np.sqrt(np.mean(voice[mask > 0] ** 2))
        bed *= (voice_rms * 10 ** (-17 / 20)) / bed_rms                 # music ~17 dB under the voice
        mix += bed * duck[:, None]
    raw = work / "mix_raw.wav"
    sf.write(raw, mix[: int(total * SR)].astype(np.float32), SR, subtype="FLOAT")

    # two-pass loudness normalization to -16 LUFS, -1.5 dBTP
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])
    aud = work / "mix.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
         f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true",
         "-ar", str(SR), str(aud)])

    srt = out.with_suffix(".srt")
    srt.write_text("".join(f"{i + 1}\n{fmt_ts(a)} --> {fmt_ts(b)}\n{c}\n\n" for i, (a, b, c) in enumerate(cues)))
    run(["ffmpeg", "-v", "error", "-y", "-i", str(vid), "-i", str(aud), "-i", str(srt),
         "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-c:s", "mov_text",
         "-metadata:s:s:0", "language=eng", "-metadata:s:a:0", "language=eng", "-movflags", "+faststart", str(out)])
    print("wrote", out, round(duration(out), 2), "s;", srt)


if __name__ == "__main__":
    main()
