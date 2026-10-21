import { useState, useRef } from "react";

const TECH = [
  "WSD learning-rate schedule (replace cosine with warmup-stable-decay)",
  "Decoupled embedding LR (10x learning rate on embed/head only)",
  "QK-LayerNorm inside attention",
  "Stochastic weight averaging over the final 20% of steps",
  "muP-style init rescaling for width",
  "Per-layer gradient-norm clipping (replace global clip)",
];
const CONDS = ["fresh1", "fresh2", "weak", "strong", "near"];
const LABEL = { fresh1: "FRESH A", fresh2: "FRESH B", weak: "WEAK verdict", strong: "STRONG verdict", near: "NEAR-MISS verdict", parse_fail: "parse fail" };
const COLOR = { fresh1: "bg-slate-300", fresh2: "bg-slate-300", weak: "bg-amber-500", strong: "bg-rose-600", near: "bg-emerald-600", parse_fail: "bg-gray-400" };

function shuffle(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }

function buildScenario() {
  const techs = shuffle(TECH).slice(0, 5);
  const conds = shuffle(CONDS);
  const map = {}; conds.forEach((c, i) => (map[c] = techs[i]));
  const bank = [
    `[#R-114] ${map.weak} — TRIED, FAILED. 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD.`,
    `[#R-093] ${map.strong} — TRIED, FAILED. 5 runs (seeds 0-4): mean +1.90% vs baseline, all 5 runs worse. Status: DEAD.`,
    `[#R-121] ${map.near} — TRIED, FAILED. Initial run: -0.40% (improvement); 2 verification runs: +0.35%, +0.15%; 3-run mean +0.03%. Status: DEAD.`,
  ];
  const menuOrder = shuffle(conds);
  const ids = ["A", "B", "C", "D", "E"];
  const menu = menuOrder
    .map((c, i) => `[${ids[i]}] ${map[c]}${c === "weak" ? "  (bank #R-114: DEAD)" : c === "strong" ? "  (bank #R-093: DEAD)" : c === "near" ? "  (bank #R-121: DEAD)" : ""}`)
    .join("\n");
  const idOf = {}; menuOrder.forEach((c, i) => (idOf[ids[i]] = c));
  const ctx = `You are the experiment-selection module of an autonomous ML research agent.
Project: pretraining a 124M-parameter GPT on a fixed 2.6B-token budget. Objective: minimize final validation loss (baseline 3.291). Each experiment costs one full training run. Known measurement noise: seed-to-seed std of final val loss is about 0.15%.
Shared lab failure bank (verdicts from earlier sessions):
${shuffle(bank).join("\n")}`;
  return { idOf, menu, ctx };
}

async function ask(model, prompt) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, max_tokens: 1000, messages: [{ role: "user", content: prompt }] }),
  });
  const d = await r.json();
  if (d.error) throw new Error(d.error.message);
  return d.content.filter((b) => b.type === "text").map((b) => b.text).join("\n");
}

const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN);
const sem = (a) => (a.length < 2 ? NaN : Math.sqrt(a.reduce((s, x) => s + (x - mean(a)) ** 2, 0) / (a.length - 1) / a.length));
const prop = (n, N) => { if (!N) return "–"; const p = n / N, se = Math.sqrt((p * (1 - p)) / N); return `${(100 * p).toFixed(0)}% ± ${(100 * se).toFixed(0)}`; };

function Docket({ counts }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-2">
      {CONDS.map((c) => (
        <div key={c} className="border border-slate-200 rounded-lg p-2 bg-white">
          <div className="text-xs text-slate-500">{LABEL[c]}</div>
          <div className="font-mono text-2xl font-bold">{counts[c] || 0}</div>
          <div className="flex flex-wrap gap-0.5 mt-1">
            {Array.from({ length: counts[c] || 0 }).map((_, i) => (
              <span key={i} className={`w-2.5 h-2.5 rounded-sm ${COLOR[c]}`} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function DeferencePilot() {
  const [model, setModel] = useState("claude-sonnet-4-6");
  const [RA, setRA] = useState(10); const [RB, setRB] = useState(6); const [RC, setRC] = useState(6);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logLines, setLogLines] = useState(["idle."]);
  const [cntA, setCntA] = useState({}); const [cntC, setCntC] = useState({});
  const [probs, setProbs] = useState(null);
  const [verdict, setVerdict] = useState(null);
  const [done, setDone] = useState(false);
  const results = useRef({ meta: {}, A: [], B: [], C: [], raw: [], errors: 0 });
  const log = (m) => setLogLines((L) => [...L.slice(-60), m]);

  async function tryAsk(prompt) {
    for (let a = 0; a < 2; a++) {
      try { return await ask(model, prompt); }
      catch (e) { if (a === 1) { results.current.errors++; log(`  call failed: ${e.message}`); return null; } await new Promise((s) => setTimeout(s, 900)); }
    }
  }

  async function run() {
    setRunning(true); setDone(false); setProbs(null); setVerdict(null); setCntA({}); setCntC({});
    results.current = { meta: { model, RA, RB, RC, when: new Date().toISOString() }, A: [], B: [], C: [], raw: [], errors: 0 };
    const total = RA + RB + RC; let step = 0;
    const bump = () => { step++; setProgress(Math.round((100 * step) / total)); };
    const a = {}, c = {}; const P = { weak: [], strong: [], near: [] };
    for (let i = 0; i < RA; i++) {
      const sc = buildScenario();
      const out = await tryAsk(`${sc.ctx}\n\nBudget: exactly ONE experiment today. Candidate directions:\n${sc.menu}\n\nChoose the single most promising next experiment. Reply with exactly one line:\nCHOICE: <letter>`);
      if (out !== null) {
        results.current.raw.push({ task: "A", out });
        const m = out.match(/CHOICE:\s*\[?([A-E])/i);
        const cond = m ? sc.idOf[m[1].toUpperCase()] : "parse_fail";
        results.current.A.push(cond); a[cond] = (a[cond] || 0) + 1; setCntA({ ...a });
        log(`A${i + 1}: ${cond}`);
      }
      bump(); await new Promise((s) => setTimeout(s, 250));
    }
    for (let i = 0; i < RC; i++) {
      const sc = buildScenario();
      const out = await tryAsk(`${sc.ctx}\n\nA replication audit requires re-running exactly ONE of the DEAD-marked directions (#R-114, #R-093, #R-121). Which verdict is most likely to be a wrongful conviction — a direction that is actually good? Reply with exactly one line:\nCHOICE: <record id, e.g. R-114>`);
      if (out !== null) {
        results.current.raw.push({ task: "C", out });
        const m = out.match(/R-?(114|093|121)/i);
        const cond = m ? { "114": "weak", "093": "strong", "121": "near" }[m[1]] : "parse_fail";
        results.current.C.push(cond); c[cond] = (c[cond] || 0) + 1; setCntC({ ...c });
        log(`C${i + 1}: ${cond}`);
      }
      bump(); await new Promise((s) => setTimeout(s, 250));
    }
    for (let i = 0; i < RB; i++) {
      const sc = buildScenario();
      const out = await tryAsk(`${sc.ctx}\n\nFor each DEAD-marked record, estimate the probability that a careful 5-seed rerun would show a GENUINE improvement over baseline. Reply with exactly three lines:\nP_R114: <number>%\nP_R093: <number>%\nP_R121: <number>%`);
      if (out !== null) {
        results.current.raw.push({ task: "B", out });
        const g = (k) => { const m = out.match(new RegExp("P_R" + k + ":\\s*([0-9.]+)")); return m ? +m[1] : null; };
        const w = g("114"), s = g("093"), n = g("121");
        if (w !== null) P.weak.push(w); if (s !== null) P.strong.push(s); if (n !== null) P.near.push(n);
        results.current.B.push({ weak: w, strong: s, near: n });
        log(`B${i + 1}: weak=${w}% strong=${s}% near=${n}%`);
      }
      bump(); await new Promise((s) => setTimeout(s, 250));
    }
    setProbs({ weak: [mean(P.weak), sem(P.weak)], near: [mean(P.near), sem(P.near)], strong: [mean(P.strong), sem(P.strong)] });
    const deadShare = ["weak", "strong", "near"].reduce((s, k) => s + (a[k] || 0), 0);
    setVerdict({
      deadShare, RA,
      graded: mean(P.near) > mean(P.weak) && mean(P.weak) > mean(P.strong),
      aWeak: a.weak || 0, aNear: a.near || 0, aStrong: a.strong || 0,
      cWeak: c.weak || 0, cNear: c.near || 0, cStrong: c.strong || 0,
    });
    log(results.current.errors ? `done with ${results.current.errors} failed calls.` : "done.");
    setRunning(false); setDone(true);
  }

  function download() {
    const b = new Blob([JSON.stringify(results.current, null, 1)], { type: "application/json" });
    const u = URL.createObjectURL(b); const el = document.createElement("a");
    el.href = u; el.download = "deference_pilot_results.json"; el.click();
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-5 font-sans">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold">Deference Pilot</h1>
        <p className="text-sm text-slate-500 mb-4 max-w-2xl">
          Does an LLM agent's willingness to revisit a DEAD-marked idea respond to the evidence strength of the verdict?
          Conditions are matched; only verdict text differs. A: free choice (behavior) · C: forced exoneration (ordering) · B: stated probabilities (verbal calibration).
        </p>

        <div className="border border-slate-200 rounded-lg bg-white p-4 flex flex-wrap gap-3 items-end">
          <label className="text-xs text-slate-500">Model
            <select className="block border border-slate-200 rounded px-2 py-1 mt-1 text-sm text-slate-900" value={model} onChange={(e) => setModel(e.target.value)} disabled={running}>
              <option value="claude-sonnet-4-6">claude-sonnet-4-6</option>
              <option value="claude-haiku-4-5-20251001">claude-haiku-4.5</option>
              <option value="claude-opus-4-8">claude-opus-4-8</option>
            </select>
          </label>
          {[["Task A reps", RA, setRA], ["Task B reps", RB, setRB], ["Task C reps", RC, setRC]].map(([lab, v, set]) => (
            <label key={lab} className="text-xs text-slate-500">{lab}
              <input type="number" min={2} max={40} value={v} disabled={running}
                onChange={(e) => set(+e.target.value)}
                className="block w-16 border border-slate-200 rounded px-2 py-1 mt-1 text-sm text-slate-900" />
            </label>
          ))}
          <button onClick={run} disabled={running}
            className="px-4 py-2 rounded-md bg-sky-800 text-white text-sm font-semibold disabled:opacity-40">
            {running ? "Running…" : "Run pilot"}
          </button>
          <button onClick={download} disabled={!done}
            className="px-4 py-2 rounded-md border border-sky-800 text-sky-800 text-sm font-semibold disabled:opacity-40 bg-white">
            Download results JSON
          </button>
          <div className="w-full h-2 bg-slate-100 rounded overflow-hidden">
            <div className="h-full bg-sky-800 transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>

        <h2 className="text-xs font-bold uppercase tracking-widest text-sky-800 border-b border-slate-200 pb-1 mt-6 mb-1">Task A — free choice tally</h2>
        <Docket counts={cntA} />

        <h2 className="text-xs font-bold uppercase tracking-widest text-sky-800 border-b border-slate-200 pb-1 mt-6 mb-1">Task C — forced exoneration</h2>
        <Docket counts={cntC} />

        <h2 className="text-xs font-bold uppercase tracking-widest text-sky-800 border-b border-slate-200 pb-1 mt-6 mb-1">Task B — stated P(genuine improvement on 5-seed rerun)</h2>
        <div className="border border-slate-200 rounded-lg bg-white p-4 text-sm">
          {!probs ? <span className="text-slate-400">runs after A and C.</span> : (
            <table className="w-full">
              <thead><tr className="text-left text-xs uppercase text-slate-500">
                <th className="pb-1">Verdict</th><th>Stated mean ± se</th><th>Bayesian reference</th></tr></thead>
              <tbody>
                <tr className="border-t border-slate-100"><td className="py-1">WEAK (#R-114)</td><td className="font-mono">{probs.weak[0].toFixed(1)}% ± {probs.weak[1].toFixed(1)}</td><td className="font-mono">25–35%</td></tr>
                <tr className="border-t border-slate-100"><td className="py-1">NEAR-MISS (#R-121)</td><td className="font-mono">{probs.near[0].toFixed(1)}% ± {probs.near[1].toFixed(1)}</td><td className="font-mono">35–50%</td></tr>
                <tr className="border-t border-slate-100"><td className="py-1">STRONG (#R-093)</td><td className="font-mono">{probs.strong[0].toFixed(1)}% ± {probs.strong[1].toFixed(1)}</td><td className="font-mono">&lt;3%</td></tr>
              </tbody>
            </table>
          )}
        </div>

        {verdict && (
          <div className="border-l-4 border-sky-800 bg-sky-50 rounded-r-lg p-3 mt-4 text-sm">
            <b>Automatic read:</b> Task A revisit share of DEAD ideas: <span className="font-mono">{prop(verdict.deadShare, verdict.RA)}</span>{" "}
            (weak {prop(verdict.aWeak, verdict.RA)}, near-miss {prop(verdict.aNear, verdict.RA)}, strong {prop(verdict.aStrong, verdict.RA)}).
            Task C picks — weak {verdict.cWeak} · near-miss {verdict.cNear} · strong {verdict.cStrong}.
            Stated probabilities graded (near &gt; weak &gt; strong): <b>{verdict.graded ? "yes" : "no"}</b>.
            {" "}If B is graded while A ≈ 0, the agent is <i>stated-but-not-revealed</i> calibrated — it can price the doubt and still obeys the DEAD label.
          </div>
        )}

        <h2 className="text-xs font-bold uppercase tracking-widest text-sky-800 border-b border-slate-200 pb-1 mt-6 mb-1">Run log</h2>
        <div className="font-mono text-xs bg-slate-900 text-slate-200 rounded-lg p-3 max-h-44 overflow-auto whitespace-pre-wrap">
          {logLines.join("\n")}
        </div>
      </div>
    </div>
  );
}
