"""Narration for the overview video. Synthesizes each beat with Kokoro (af_heart) and writes
timeline.json: per scene, the start time and duration of every beat relative to the scene start.
Usage: python3 narration.py   (needs models/kokoro-v1.0.onnx and models/voices-v1.0.bin)"""
import json, os, hashlib
import numpy as np, soundfile as sf

VOICE, SPEED, SR = "af_heart", 0.97, 24000
LEAD, GAP, TAIL = 0.6, 0.45, 1.2      # seconds: before first beat, between beats, after last beat

# (scene, [(spoken text, extra hold after this beat in seconds), ...])
SCRIPT = [
    ("title", [
        ("Wrongful convictions in shared failure banks.", 0.3),
        ("Why the memory of failure in automated science should keep its evidence.", 0.6),
    ]),
    ("bank", [
        ("Autonomous research agents increasingly share a failure bank.", 0.4),
        ("Every failed experiment is written down once, so no agent wastes budget repeating it.", 0.6),
        ("That sounds sensible. But each failure verdict is a statistical claim, usually made from one small, noisy experiment.", 0.3),
    ]),
    ("noise", [
        ("Take an idea that is genuinely good, but only slightly.", 0.3),
        ("Measure it once, and the result scatters around its small true effect.", 1.6),
        ("About a third of the time, the measurement lands below zero. The idea fails, and the bank marks it dead.", 0.6),
        ("Marginally good ideas are exactly the ones a single noisy test is most likely to convict.", 0.3),
    ]),
    ("asym", [
        ("And the two possible errors are not symmetric.", 0.2),
        ("A bad idea that is wrongly kept gets built on. Its descendants keep failing, and the mistake exposes itself.", 0.5),
        ("A good idea that is wrongly killed is never tried again. When new ideas grow from confirmed ones, none of its descendants are ever generated.", 0.6),
        ("False positives expose themselves. False negatives never do.", 0.3),
    ]),
    ("measured", [
        ("How often does this happen in practice?", 0.2),
        ("In a live training loop for a small character-level GPT, seventeen and a half percent of convictions were wrongful, close to the nineteen percent our theory predicts.", 0.4),
        ("Among near-miss ideas, ones that passed once and then failed verification, between a third and a half of the verdicts were wrong.", 0.4),
        ("And replaying a hundred and twenty-two thousand convictions on the public F C Net benchmark shows the same shape: the errors concentrate on small, genuine improvements.", 0.3),
    ]),
    ("llm", [
        ("Do language-model agents look past the label?", 0.2),
        ("We showed models the same one-run record, labeled either dead, or inconclusive.", 0.3),
        ("Labeled inconclusive, three Claude models put the chance the idea is genuinely better at thirty-two and a half percent. Labeled dead: eight and a half.", 0.5),
        ("Across twelve models from nine families, agents choosing their next experiment revisited none of ninety-four dead-marked ideas. And every family picked the best available idea less often once it carried the label.", 0.4),
        ("The models can price the evidence. The label overrides it.", 0.3),
    ]),
    ("fix", [
        ("The fix is a change of schema. It needs no new model.", 0.2),
        ("Instead of a bare dead flag, each record carries its evidence: the number of runs, the measured effect, and the noise.", 0.3),
        ("From that, the bank computes the probability that the idea is truly dead. One run, slightly worse: zero point seven nine. That is below the threshold, so the idea stays open, and a retry is allowed.", 0.5),
        ("Five runs, averaging the same deficit: zero point nine six. Now the lock is earned.", 0.5),
        ("It is a standard confidence rule. Shared failure banks just don't implement it.", 0.3),
    ]),
    ("result", [
        ("Does it matter end to end? We ran a closed research loop with real training runs: eight independent loops for each memory rule.", 0.3),
        ("With no memory, with binary locks, or with a parole rule, each loop found about forty-six truth-validated discoveries.", 0.4),
        ("With evidence-graded records: sixty point five. That is thirty to thirty-two percent more; a difference of thirteen point nine, with a ninety-five percent interval from nine point seven to eighteen point one.", 0.5),
        ("It does not hold everywhere. In a low-noise, short-horizon loop, binary locking edges ahead, and with language-model proposers, the ordering depends on the proposer.", 0.4),
    ]),
    ("end", [
        ("Records that carry their evidence. Locks that require it.", 0.5),
        ("The code, logs, and cached runs are on GitHub.", 0.4),
    ]),
]

def main():
    from kokoro_onnx import Kokoro
    os.makedirs("audio", exist_ok=True)
    k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
    timeline = {}
    for scene, beats in SCRIPT:
        t, out = LEAD, []
        for i, (text, hold) in enumerate(beats):
            h = hashlib.md5(f"{VOICE}|{SPEED}|{text}".encode()).hexdigest()[:10]
            path = f"audio/{scene}_{i}_{h}.wav"
            if not os.path.exists(path):
                s, sr = k.create(text, voice=VOICE, speed=SPEED, lang="en-us")
                s = np.asarray(s, np.float32)
                nz = np.where(np.abs(s) > 0.01)[0]                 # trim leading/trailing silence
                s = s[max(nz[0] - 240, 0): nz[-1] + 3600]      # keep 150 ms of natural decay
                f = 1440; s[-f:] *= np.linspace(1, 0, f) ** 2      # 60 ms fade-out
                sf.write(path, s, sr)
            dur = sf.info(path).duration
            out.append({"text": text, "wav": path, "start": round(t, 3), "dur": round(dur, 3)})
            t += dur + GAP + hold
        total = t - GAP + TAIL
        timeline[scene] = {"beats": out, "total": round(total, 3)}
        print(f"{scene:9s} {total:6.1f}s  " + " ".join(f"{b['dur']:.1f}" for b in out))
    json.dump(timeline, open("timeline.json", "w"), indent=1)
    print("total", round(sum(v["total"] for v in timeline.values()), 1), "s")

if __name__ == "__main__":
    main()
