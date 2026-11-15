// Check that the browser engine matches the Python model on the held-out test sets (run with node).
const fs = require("fs");
const path = require("path");
const Q = require("./qalaisyn.js");

const base = path.join(__dirname, "model") + path.sep;
const fetchFn = async f => ({ ok: true, text: async () => fs.readFileSync(f, "utf8"),
  arrayBuffer: async () => { const b = fs.readFileSync(f); return b.buffer.slice(b.byteOffset, b.byteOffset + b.length); } });

function ed(a, b) {
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) cur.push(Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] !== b[j - 1])));
    prev = cur;
  }
  return prev[b.length];
}

(async () => {
  let t = Date.now();
  const eng = await Q.load(base, fetchFn);
  console.log(`loaded in ${Date.now() - t} ms, words ${eng.words.length}`);
  const P = path.join(__dirname, "..", "data", "processed");
  const sets = [["restored_test_tatoeba_cyr.jsonl", 1e9], ["restored_test_flores_cyr.jsonl", 800],
    ["restored_test_tatoeba.jsonl", 1e9], ["restored_test_tatoeba_cyr-typos-15.jsonl", 1e9]];
  const res = {};
  for (const [f, n] of sets) {
    const rows = fs.readFileSync(path.join(P, f), "utf8").trim().split("\n").slice(0, n).map(JSON.parse);
    let ej = 0, ep = 0, nw = 0, same = 0;
    t = Date.now();
    for (const r of rows) {
      const h = eng.restore(r.chat);
      const g = r.gold.split(" ");
      ej += ed(h.split(" "), g); ep += ed(r["M2 Qalaisyn+typos"].split(" "), g); nw += g.length;
      same += h === r["M2 Qalaisyn+typos"];
    }
    res[f] = { browser_wer: ej / nw, python_wer: ep / nw, identical: same / rows.length };
    console.log(`${f}: browser WER ${(100 * ej / nw).toFixed(2)}%  python WER ${(100 * ep / nw).toFixed(2)}%  ` +
      `identical outputs ${(100 * same / rows.length).toFixed(1)}%  ${((Date.now() - t) / rows.length).toFixed(1)} ms/msg`);
  }
  const c = eng.restoreWithConfidence("салем калайсын ертен мектепке барасын ба");
  console.log(c.map(w => `${w.word}(${w.confidence.toFixed(2)})`).join(" "));
  fs.writeFileSync(path.join(__dirname, "..", "results", "browser_engine.json"), JSON.stringify(res, null, 2));
})();
