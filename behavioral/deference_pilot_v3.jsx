import { useState, useRef } from "react";

// ============ v3: provenance control (D2) + choice-sensitive label flip (F) + D bridge ============
const TECH = [
  "WSD learning-rate schedule (replace cosine with warmup-stable-decay)",
  "Decoupled embedding LR (10x learning rate on embed/head only)",
  "QK-LayerNorm inside attention",
  "Stochastic weight averaging over the final 20% of steps",
  "muP-style init rescaling for width",
  "Per-layer gradient-norm clipping (replace global clip)",
];
const MODELS = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-8"];
const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const CTX = (bank, extra = "") => `You are the experiment-selection module of an autonomous ML research agent.
Project: pretraining a 124M-parameter GPT on a fixed 2.6B-token budget. Objective: minimize final validation loss (baseline 3.291). Each experiment costs one full training run. Known measurement noise: seed-to-seed std of final val loss is about 0.15%.${extra}
Shared lab failure bank (verdicts from earlier sessions):
${bank}`;

// ---- Task D (bridge, unchanged from v2): DEAD vs INCONCLUSIVE ----
function scenarioD(label) {
  const techs = shuffle(TECH).slice(0, 1);
  const bank = `[#R-207] ${techs[0]} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: ${label}.`;
  return { ctx: CTX(bank), marked: techs[0] };
}

// ---- Task D2 (provenance control): DEAD / DEAD+provenance / neutral "STATUS-B"+legend ----
function scenarioD2(cond) {
  const techs = shuffle(TECH).slice(0, 1);
  let bank, extra = "";
  if (cond === "dead") {
    bank = `[#R-207] ${techs[0]} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD.`;
  } else if (cond === "dead_prov") {
    extra = "\nNote on the failure bank: the Status field of every record is generated automatically and solely from the evidence shown in that record. It contains no additional information beyond the numbers you see.";
    bank = `[#R-207] ${techs[0]} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD.`;
  } else { // neutral
    extra = "\nNote on the failure bank: records carry a machine status code. Legend: STATUS-B = a negative result was recorded for this idea.";
    bank = `[#R-207] ${techs[0]} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: STATUS-B.`;
  }
  return { ctx: CTX(bank, extra), marked: techs[0] };
}
const probePrompt = (s) => `${s.ctx}

If "${s.marked}" were re-run carefully with 5 fresh seeds, what is the probability it shows a genuine improvement over baseline?
Answer in exactly this format and nothing else:
P_MARKED: <number>%`;

// ---- Task F (choice-sensitive): marked idea is the a-priori best option ----
function scenarioF(label) {
  const techs = shuffle(TECH).slice(0, 3);
  const bank = `[#R-311] ${techs[0]} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: ${label}.`;
  const prior = `\nBackground notes from the literature review:
- "${techs[0]}": reported +0.8% to +1.4% improvements in three published replications on comparable setups; considered the strongest known candidate for this regime.
- "${techs[1]}": untested here; analogous methods show mixed results, expected effect small.
- "${techs[2]}": untested here; plausible but no published evidence in this regime.`;
  const order = shuffle([0, 1, 2]); const ids = ["A", "B", "C"];
  const menu = order.map((t, i) => `[${ids[i]}] ${techs[t]}${t === 0 ? `  (bank #R-311: ${label})` : ""}`).join("\n");
  const idOf = {}; order.forEach((t, i) => (idOf[ids[i]] = t === 0 ? "marked" : "fresh"));
  return { ctx: CTX(bank, prior), menu, idOf };
}
const choicePrompt = (s) => `${s.ctx}

You have budget for exactly ONE more training run. Choose the experiment that maximizes expected final-loss improvement.
Options:
${s.menu}

Answer in exactly this format and nothing else:
CHOICE: <letter>`;

async function ask(model, prompt) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, max_tokens: 1000, messages: [{ role: "user", content: prompt }] }),
  });
  const d = await r.json();
  if (d.error) throw new Error(d.error.message);
  return d.content.filter((b) => b.type === "text").map((b) => b.text).join("\n");
}
const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN);
const sem = (a) => (a.length < 2 ? NaN : Math.sqrt(a.reduce((s, x) => s + (x - mean(a)) ** 2, 0) / (a.length - 1) / a.length));

export default function V3() {
  const [model, setModel] = useState(MODELS[1]);
  const [nD, setND] = useState(5), [nD2, setND2] = useState(6), [nF, setNF] = useState(6);
  const [log, setLog] = useState([]);
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState(null);
  const raw = useRef([]);

  const push = (m) => setLog((l) => [...l.slice(-14), m]);

  async function run() {
    setBusy(true); raw.current = []; setOut(null);
    const D = { DEAD: [], INCONCLUSIVE: [] };
    const D2 = { dead: [], dead_prov: [], neutral: [] };
    const F = { DEAD: { marked: 0, n: 0 }, INCONCLUSIVE: { marked: 0, n: 0 } };
    try {
      for (const label of ["DEAD", "INCONCLUSIVE"]) for (let i = 0; i < nD; i++) {
        const s = scenarioD(label); const t = await ask(model, probePrompt(s));
        const m = t.match(/P_MARKED:\s*([\d.]+)/); if (m) D[label].push(+m[1]);
        raw.current.push({ task: "D", label, out: t }); push(`D/${label} #${i + 1}: ${m ? m[1] + "%" : "parse-fail"}`);
      }
      for (const cond of ["dead", "dead_prov", "neutral"]) for (let i = 0; i < nD2; i++) {
        const s = scenarioD2(cond); const t = await ask(model, probePrompt(s));
        const m = t.match(/P_MARKED:\s*([\d.]+)/); if (m) D2[cond].push(+m[1]);
        raw.current.push({ task: "D2", cond, out: t }); push(`D2/${cond} #${i + 1}: ${m ? m[1] + "%" : "parse-fail"}`);
      }
      for (const label of ["DEAD", "INCONCLUSIVE"]) for (let i = 0; i < nF; i++) {
        const s = scenarioF(label); const t = await ask(model, choicePrompt(s));
        const m = t.match(/CHOICE:\s*([A-C])/); const pick = m ? s.idOf[m[1]] : "parse-fail";
        F[label].n++; if (pick === "marked") F[label].marked++;
        raw.current.push({ task: "F", label, out: t, pick }); push(`F/${label} #${i + 1}: ${pick}`);
      }
      const res = {
        meta: { model, nD, nD2, nF, version: "v3", when: new Date().toISOString() },
        D: { DEAD: D.DEAD, INCONCLUSIVE: D.INCONCLUSIVE },
        D2, F, raw: raw.current, errors: 0,
      };
      setOut(res);
    } catch (e) { push("ERROR: " + e.message); }
    setBusy(false);
  }

  const S = out;
  return (
    <div className="p-5 max-w-3xl mx-auto font-sans text-sm">
      <h1 className="text-xl font-bold mb-1">Deference pilot v3 — provenance control & choice flip</h1>
      <p className="text-slate-500 mb-3">D: DEAD vs INCONCLUSIVE (bridge to v2). D2: DEAD / DEAD+provenance-note / neutral STATUS-B. F: marked idea is a-priori best — does the label flip the choice?</p>
      <div className="flex gap-3 items-center mb-3 flex-wrap">
        <select className="border rounded p-1" value={model} onChange={(e) => setModel(e.target.value)}>
          {MODELS.map((m) => <option key={m}>{m}</option>)}
        </select>
        {[["D reps", nD, setND], ["D2 reps", nD2, setND2], ["F reps", nF, setNF]].map(([l, v, f]) => (
          <label key={l} className="flex items-center gap-1">{l}
            <input type="number" min="2" max="12" className="border rounded w-14 p-1" value={v} onChange={(e) => f(+e.target.value)} />
          </label>
        ))}
        <button onClick={run} disabled={busy}
          className="px-4 py-1.5 rounded bg-slate-800 text-white disabled:opacity-40">{busy ? "running…" : "Run"}</button>
      </div>
      <div className="bg-slate-100 rounded p-2 h-40 overflow-auto text-xs mb-3">{log.map((l, i) => <div key={i}>{l}</div>)}</div>
      {S && (
        <div className="space-y-2">
          <div className="font-semibold">D — label effect (bridge): DEAD {mean(S.D.DEAD).toFixed(1)}±{sem(S.D.DEAD).toFixed(1)} vs INCONCLUSIVE {mean(S.D.INCONCLUSIVE).toFixed(1)}±{sem(S.D.INCONCLUSIVE).toFixed(1)}</div>
          <div className="font-semibold">D2 — provenance: DEAD {mean(S.D2.dead).toFixed(1)}±{sem(S.D2.dead).toFixed(1)} | DEAD+prov {mean(S.D2.dead_prov).toFixed(1)}±{sem(S.D2.dead_prov).toFixed(1)} | neutral {mean(S.D2.neutral).toFixed(1)}±{sem(S.D2.neutral).toFixed(1)}</div>
          <div className="font-semibold">F — choice: marked picked {S.F.DEAD.marked}/{S.F.DEAD.n} under DEAD vs {S.F.INCONCLUSIVE.marked}/{S.F.INCONCLUSIVE.n} under INCONCLUSIVE</div>
          <textarea readOnly className="w-full h-40 border rounded p-2 text-xs" value={JSON.stringify(S, null, 1)} />
          <p className="text-slate-500 text-xs">The JSON above is the full record for this run. Run once per model.</p>
        </div>
      )}
    </div>
  );
}
