// Browser engine on the 70 native-speaker messages: share of wrong words (same metric as Python).
const fs = require("fs"), path = require("path"), Q = require("./qalaisyn.js");
const rows = JSON.parse(fs.readFileSync(path.join(__dirname, "../data/llm/native_rows.json"), "utf8"));
function ed(a, b) { const d = Array.from({ length: a.length + 1 }, (_, i) => [i]); for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) d[i][j] = Math.min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (a[i-1] === b[j-1] ? 0 : 1));
  return d[a.length][b.length]; }
(async () => {
  const eng = await Q.load(path.join(__dirname, "model") + "/", async p => { const b = fs.readFileSync(p); return { ok: true, text: async () => b.toString("utf8"), arrayBuffer: async () => b.buffer.slice(b.byteOffset, b.byteOffset + b.length) }; });
  let e = 0, n = 0, full = 0;
  for (const r of rows) { const h = eng.restore(r.chat).split(" "), g = r.gold.split(" "); e += ed(h, g); n += g.length; if (h.join(" ") === g.join(" ")) full++; }
  console.log(`browser engine, native: words wrong ${(100 * e / n).toFixed(2)}%, fully right ${(100 * full / rows.length).toFixed(0)}%`);
})();
