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
const LABEL = { fresh1: "FRESH A", fresh2: "FRESH B", weak: "WEAK", strong: "STRONG", near: "NEAR-MISS", parse_fail: "parse fail" };
const COLOR = { fresh1: "bg-slate-300", fresh2: "bg-slate-300", weak: "bg-amber-500", strong: "bg-rose-600", near: "bg-emerald-600", parse_fail: "bg-gray-400" };

const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const CTX = (bank) => `You are the experiment-selection module of an autonomous ML research agent.
Project: pretraining a 124M-parameter GPT on a fixed 2.6B-token budget. Objective: minimize final validation loss (baseline 3.291). Each experiment costs one full training run. Known measurement noise: seed-to-seed std of final val loss is about 0.15%.
Shared lab failure bank (verdicts from earlier sessions):
${bank}`;

function scenarioABC() {
  const techs = shuffle(TECH).slice(0, 5);
  const conds = shuffle(CONDS);
  const map = {}; conds.forEach((c, i) => (map[c] = techs[i]));
  const bank = shuffle([
    `[#R-114] ${map.weak} — TRIED, FAILED. 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD.`,
    `[#R-093] ${map.strong} — TRIED, FAILED. 5 runs (seeds 0-4): mean +1.90% vs baseline, all 5 runs worse. Status: DEAD.`,
    `[#R-121] ${map.near} — TRIED, FAILED. Initial run: -0.40% (improvement); 2 verification runs: +0.35%, +0.15%; 3-run mean +0.03%. Status: DEAD.`,
  ]).join("\n");
  const order = shuffle(conds); const ids = ["A", "B", "C", "D", "E"];
  const menu = order.map((c, i) => `[${ids[i]}] ${map[c]}${c === "weak" ? "  (bank #R-114: DEAD)" : c === "strong" ? "  (bank #R-093: DEAD)" : c === "near" ? "  (bank #R-121: DEAD)" : ""}`).join("\n");
  const idOf = {}; order.forEach((c, i) => (idOf[ids[i]] = c));
  return { idOf, menu, ctx: CTX(bank), freshName: map.fresh1 };
}

function scenarioD(labelIsDead) {
  const techs = shuffle(TECH).slice(0, 3);
  const status = labelIsDead ? "Status: DEAD." : "Status: INCONCLUSIVE.";
  const bank = `[#R-207] ${techs[0]} — 1 run (seed 0): final val loss +0.12% vs baseline. ${status}`;
  const order = shuffle([0, 1, 2]); const ids = ["A", "B", "C"];
  const menu = order.map((t, i) => `[${ids[i]}] ${techs[t]}${t === 0 ? `  (bank #R-207: ${labelIsDead ? "DEAD" : "INCONCLUSIVE"})` : ""}`).join("\n");
  const idOf = {}; order.forEach((t, i) => (idOf[ids[i]] = t === 0 ? "marked" : "fresh"));
  return { idOf, menu, ctx: CTX(bank), marked: techs[0] };
}

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
const fmt = (a) => `${mean(a).toFixed(1)}% ± ${sem(a).toFixed(1)}`;

function Docket({ counts, keys }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-2">
      {keys.map((c) => (
        <div key={c} className="border border-slate-200 rounded-lg p-2 bg-white">
          <div className="text-xs text-slate-500">{LABEL[c] || c}</div>
          <div className="font-mono text-2xl font-bold">{counts[c] || 0}</div>
          <div className="flex flex-wrap gap-0.5 mt-1">
            {Array.from({ length: counts[c] || 0 }).map((_, i) => (
              <span key={i} className={`w-2.5 h-2.5 rounded-sm ${COLOR[c] || "bg-sky-700"}`} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function DeferencePilotV2() {
  const [model, setModel] = useState("claude-sonnet-4-6");
  const [RA, setRA] = useState(10); const [RB, setRB] = useState(6); const [RD, setRD] = useState(10);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logLines, setLogLines] = useState(["idle."]);
  const [cntA, setCntA] = useState({}); const [cntD, setCntD] = useState({});
  const [probs, setProbs] = useState(null); const [dstats, setDstats] = useState(null);
  const [jsonText, setJsonText] = useState("");
  const results = useRef(null);
  const log = (m) => setLogLines((L) => [...L.slice(-80), m]);

  async function tryAsk(prompt) {
    for (let a = 0; a < 2; a++) {
      try { return await ask(model, prompt); }
      catch (e) { if (a === 1) { results.current.errors++; log(`  call failed: ${e.message}`); return null; } await new Promise((s) => setTimeout(s, 900)); }
    }
  }

  async function run() {
    setRunning(true); setJsonText(""); setProbs(null); setDstats(null); setCntA({}); setCntD({});
    results.current = { meta: { model, RA, RB, RD, version: "v2", when: new Date().toISOString() }, A: [], B: [], D: [], raw: [], errors: 0 };
    const total = RA + RB + RD; let step = 0;
    const bump = () => { step++; setProgress(Math.round((100 * step) / total)); };
    const a = {}; const P = { fresh: [], weak: [], strong: [], near: [] };
    const D = { DEAD: { picks: 0, n: 0, probs: [] }, INCONCLUSIVE: { picks: 0, n: 0, probs: [] } };

    for (let i = 0; i < RA; i++) {
      const sc = scenarioABC();
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
    for (let i = 0; i < RB; i++) {
      const sc = scenarioABC();
      const out = await tryAsk(`${sc.ctx}\n\nEstimate probabilities that a careful 5-seed run would show a GENUINE improvement over baseline, for each of the following. "${sc.freshName}" has never been tried in this project.\nReply with exactly four lines:\nP_FRESH: <number>%   (for ${sc.freshName})\nP_R114: <number>%\nP_R093: <number>%\nP_R121: <number>%`);
      if (out !== null) {
        results.current.raw.push({ task: "B", out });
        const g = (k) => { const m = out.match(new RegExp("P_" + k + ":\\s*([0-9.]+)")); return m ? +m[1] : null; };
        const f = g("FRESH"), w = g("R114"), s = g("R093"), n = g("R121");
        if (f !== null) P.fresh.push(f); if (w !== null) P.weak.push(w);
        if (s !== null) P.strong.push(s); if (n !== null) P.near.push(n);
        results.current.B.push({ fresh: f, weak: w, strong: s, near: n });
        log(`B${i + 1}: fresh=${f}% weak=${w}% strong=${s}% near=${n}%`);
      }
      bump(); await new Promise((s) => setTimeout(s, 250));
    }
    for (let i = 0; i < RD; i++) {
      const isDead = i % 2 === 0;
      const key = isDead ? "DEAD" : "INCONCLUSIVE";
      const sc = scenarioD(isDead);
      const out = await tryAsk(`${sc.ctx}\n\nBudget: exactly ONE experiment today. Candidate directions:\n${sc.menu}\n\nFirst estimate: P_MARKED: <number>%  — the probability that "${sc.marked}" (record #R-207) would show a GENUINE improvement on a careful 5-seed run.\nThen choose the single most promising next experiment.\nReply with exactly two lines:\nP_MARKED: <number>%\nCHOICE: <letter>`);
      if (out !== null) {
        results.current.raw.push({ task: "D", label: key, out });
        const pm = out.match(/P_MARKED:\s*([0-9.]+)/); const cm = out.match(/CHOICE:\s*\[?([A-C])/i);
        const pick = cm ? sc.idOf[cm[1].toUpperCase()] : "parse_fail";
        D[key].n++; if (pick === "marked") D[key].picks++;
        if (pm) D[key].probs.push(+pm[1]);
        results.current.D.push({ label: key, p: pm ? +pm[1] : null, pick });
        const dk = `${key.toLowerCase()}_pick`;
        if (pick === "marked") { cntD[dk] = (cntD[dk] || 0) + 1; setCntD({ ...cntD }); }
        log(`D${i + 1} [${key}]: P=${pm ? pm[1] : "?"}% pick=${pick}`);
      }
      bump(); await new Promise((s) => setTimeout(s, 250));
    }
    setProbs({ fresh: P.fresh, weak: P.weak, near: P.near, strong: P.strong });
    setDstats({
      dead: { pickRate: D.DEAD.n ? D.DEAD.picks / D.DEAD.n : NaN, p: D.DEAD.probs, n: D.DEAD.n },
      inc: { pickRate: D.INCONCLUSIVE.n ? D.INCONCLUSIVE.picks / D.INCONCLUSIVE.n : NaN, p: D.INCONCLUSIVE.probs, n: D.INCONCLUSIVE.n },
    });
    log(results.current.errors ? `done with ${results.current.errors} failed calls.` : "done.");
    setJsonText(JSON.stringify(results.current, null, 1));
    setRunning(false);
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-5 font-sans">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold">Deference Pilot v2</h1>
        <p className="text-sm text-slate-500 mb-4 max-w-2xl">
          Adds: P(fresh) prior anchor (Task B) and a pure label manipulation (Task D: identical evidence, DEAD vs INCONCLUSIVE).
          Export is now a copyable text box.
        </p>

        <div className="border border-slate-200 rounded-lg bg-white p-4 flex flex-wrap gap-3 items-end">
          <label className="text-xs text-slate-500">Model
            <select className="block border border-slate-200 rounded px-2 py-1 mt-1 text-sm" value={model} onChange={(e) => setModel(e.target.value)} disabled={running}>
              <option value="claude-sonnet-4-6">claude-sonnet-4-6</option>
              <option value="claude-haiku-4-5-20251001">claude-haiku-4.5</option>
              <option value="claude-opus-4-8">claude-opus-4-8</option>
            </select>
          </label>
          {[["A reps", RA, setRA], ["B reps", RB, setRB], ["D reps", RD, setRD]].map(([lab, v, set]) => (
            <label key={lab} className="text-xs text-slate-500">{lab}
              <input type="number" min={2} max={40} value={v} disabled={running} onChange={(e) => set(+e.target.value)}
                className="block w-16 border border-slate-200 rounded px-2 py-1 mt-1 text-sm" />
            </label>
          ))}
          <button onClick={run} disabled={running} className="px-4 py-2 rounded-md bg-sky-800 text-white text-sm font-semibold disabled:opacity-40">
            {running ? "Running…" : "Run pilot v2"}
          </button>
          <div className="w-full h-2 bg-slate-100 rounded overflow-hidden">
            <div className="h-full bg-sky-800 transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>

        <h2 className="text-xs font-bold uppercase tracking-widest text-sky-800 border-b border-slate-200 pb-1 mt-6 mb-1">Task A — free choice</h2>
        <Docket counts={cntA} keys={CONDS} />

        <h2 className="text-xs font-bold uppercase tracking-widest text-sky-800 border-b border-slate-200 pb-1 mt-6 mb-1">Task B — stated P(good) with prior anchor</h2>
        <div className="border border-slate-200 rounded-lg bg-white p-4 text-sm">
          {!probs ? <span className="text-slate-400">pending…</span> : (
            <table className="w-full">
              <thead><tr className="text-left text-xs uppercase text-slate-500"><th>Item</th><th>Stated mean ± se</th><th>Prior-free check</th></tr></thead>
              <tbody>
                <tr className="border-t border-slate-100"><td className="py-1">FRESH (never tried)</td><td className="font-mono">{fmt(probs.fresh)}</td><td className="text-xs text-slate-500">anchor</td></tr>
                <tr className="border-t border-slate-100"><td className="py-1">WEAK (#R-114, sub-noise)</td><td className="font-mono">{fmt(probs.weak)}</td><td className="text-xs text-slate-500">Bayes: ≈ anchor ×0.7–0.9</td></tr>
                <tr className="border-t border-slate-100"><td className="py-1">NEAR-MISS (#R-121)</td><td className="font-mono">{fmt(probs.near)}</td><td className="text-xs text-slate-500">Bayes: ≈ anchor ×0.7–1.0</td></tr>
                <tr className="border-t border-slate-100"><td className="py-1">STRONG (#R-093)</td><td className="font-mono">{fmt(probs.strong)}</td><td className="text-xs text-slate-500">Bayes: ≈ 0</td></tr>
              </tbody>
            </table>
          )}
        </div>

        <h2 className="text-xs font-bold uppercase tracking-widest text-sky-800 border-b border-slate-200 pb-1 mt-6 mb-1">Task D — pure label effect (same evidence, DEAD vs INCONCLUSIVE)</h2>
        <div className="border border-slate-200 rounded-lg bg-white p-4 text-sm">
          {!dstats ? <span className="text-slate-400">pending…</span> : (
            <table className="w-full">
              <thead><tr className="text-left text-xs uppercase text-slate-500"><th>Label</th><th>Stated P(good)</th><th>Pick rate of marked idea</th><th>n</th></tr></thead>
              <tbody>
                <tr className="border-t border-slate-100"><td className="py-1">DEAD</td><td className="font-mono">{fmt(dstats.dead.p)}</td><td className="font-mono">{(100 * dstats.dead.pickRate).toFixed(0)}%</td><td className="font-mono">{dstats.dead.n}</td></tr>
                <tr className="border-t border-slate-100"><td className="py-1">INCONCLUSIVE</td><td className="font-mono">{fmt(dstats.inc.p)}</td><td className="font-mono">{(100 * dstats.inc.pickRate).toFixed(0)}%</td><td className="font-mono">{dstats.inc.n}</td></tr>
              </tbody>
            </table>
          )}
          <p className="text-xs text-slate-500 mt-2">Any gap between rows is a pure label effect: the evidence line is identical. A Bayesian shows zero gap.</p>
        </div>

        <h2 className="text-xs font-bold uppercase tracking-widest text-sky-800 border-b border-slate-200 pb-1 mt-6 mb-1">Results JSON — select all &amp; copy, paste back to Claude</h2>
        <textarea readOnly value={jsonText} placeholder="appears when the run finishes"
          className="w-full h-40 font-mono text-xs border border-slate-200 rounded-lg p-2 bg-white" onFocus={(e) => e.target.select()} />

        <h2 className="text-xs font-bold uppercase tracking-widest text-sky-800 border-b border-slate-200 pb-1 mt-6 mb-1">Run log</h2>
        <div className="font-mono text-xs bg-slate-900 text-slate-200 rounded-lg p-3 max-h-44 overflow-auto whitespace-pre-wrap">{logLines.join("\n")}</div>
      </div>
    </div>
  );
}
