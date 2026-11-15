// Qalaisyn engine in JavaScript: the same method as src/restore.py (M2), running in the browser.
// Candidate words + typing-habit model + word-bigram language model (Witten-Bell) + Viterbi,
// forward-backward confidence, typo search, Russian words and merged question particles.
(function (root) {
  "use strict";

  const CANON = {"а":"a","ә":"a","б":"b","в":"v","г":"g","ғ":"g","д":"d","е":"e","э":"e","ж":"j","з":"z","и":"i","й":"i",
    "і":"i","ы":"i","к":"k","қ":"k","л":"l","м":"m","н":"n","ң":"n","о":"o","ө":"o","п":"p","р":"r","с":"s","т":"t",
    "у":"u","ұ":"u","ү":"u","ф":"f","х":"h","һ":"h","ц":"c","ч":"C","ш":"S","щ":"S","ъ":"","ь":"","ю":"iu","я":"ia",
    "ё":"io","-":"-"};
  const MULTI = [["sh",["S"]],["zh",["j"]],["ch",["C"]],["gh",["g"]],["ts",["c","ts"]],["ng",["n","ng"]]];
  const SINGLE = {"q":["k"],"ä":["a"],"ö":["o"],"ü":["u"],"ı":["i"],"y":["i"],"ğ":["g"],"ñ":["n"],"ş":["S"],
    "x":["h"],"w":["S","u","v"],"c":["c","C","s"],"j":["j"]};
  const STRICT = {"q":"қ","ä":"ә","ö":"ө","ü":"ү","ğ":"ғ","ñ":"ң","ı":"ы","ş":"ш"};
  const KZ = "әғқңөұүһі";
  const MARKERS = {"қ":"qқ","ә":"äә","ө":"öө","ү":"üү","ғ":"ğғ","ң":"ñң","ұ":"ұ","і":"і","һ":"һ"};
  const PARTICLES = new Set(["ма","ме","ба","бе","па","пе","ma","me","ba","be","pa","pe"]);
  const CONTRACTIONS = {"жатм":"жатырмын","жатрм":"жатырмын","жатырм":"жатырмын","jatm":"жатырмын",
    "jatyrm":"жатырмын","zhatyrm":"жатырмын"};
  const RULE_MULTI = [["sh","ш"],["zh","ж"],["ch","ч"],["gh","ғ"],["ts","ц"],["yu","ю"],["ya","я"],["yo","ё"],["ng","ң"]];
  const RULE_SINGLE = {"a":"а","b":"б","c":"ц","d":"д","e":"е","f":"ф","g":"г","h":"х","i":"і","j":"ж","k":"к","l":"л",
    "m":"м","n":"н","o":"о","p":"п","q":"қ","r":"р","s":"с","t":"т","u":"у","v":"в","w":"у","x":"х","y":"ы","z":"з",
    "ä":"ә","ö":"ө","ü":"ү","ğ":"ғ","ñ":"ң","ı":"ы","ş":"ш"};
  const LATIN = {"а":"a","ә":"ä","б":"b","в":"v","г":"g","ғ":"ğ","д":"d","е":"e","ё":"io","ж":"j","з":"z","и":"i",
    "й":"i","к":"k","қ":"q","л":"l","м":"m","н":"n","ң":"ñ","о":"o","ө":"ö","п":"p","р":"r","с":"s","т":"t","у":"u",
    "ұ":"ū","ү":"ü","ф":"f","х":"h","һ":"h","ц":"ts","ч":"ç","ш":"ş","щ":"şş","ъ":"","ы":"y","і":"ı","ь":"","э":"e",
    "ю":"iu","я":"ia"};
  const SKEL = "abvgdejzik lmnoprstufhcCS".replace(" ", "").split("");
  const HABIT = Math.log(0.1), TYPO = Math.log(0.002), OOV = -12.0, TOP = 25, FUZZY_BELOW = 5;

  const clean = t => t.toLowerCase().replace(/['`’]/g, "");
  const canonWord = w => Array.from(w).map(ch => (ch in CANON ? CANON[ch] : ch)).join("");
  const count = (s, ch) => s.split(ch).length - 1;
  const lse = xs => { const m = Math.max(...xs); return m + Math.log(xs.reduce((a, x) => a + Math.exp(x - m), 0)); };

  function chatVariants(tok, limit = 32) {
    const t = clean(tok);
    let res = [""];
    for (let i = 0; i < t.length;) {
      let opts = null, step = 1;
      for (const [pat, outs] of MULTI) if (t.startsWith(pat, i)) { opts = outs; step = pat.length; break; }
      if (!opts) {
        const ch = t[i];
        opts = SINGLE[ch] || (ch in CANON ? [CANON[ch]] : [ch]);
      }
      const nxt = [];
      for (const r of res) for (const o of opts) { if (nxt.length < limit) nxt.push(r + o); }
      res = nxt;
      i += step;
    }
    return res;
  }

  function ruleWord(tok) {
    const t = clean(tok);
    if (/^\d+$/.test(t)) return t;
    let out = "";
    for (let i = 0; i < t.length;) {
      let hit = false;
      for (const [pat, cyr] of RULE_MULTI) if (t.startsWith(pat, i)) { out += cyr; i += pat.length; hit = true; break; }
      if (!hit) { out += RULE_SINGLE[t[i]] || t[i]; i += 1; }
    }
    return out;
  }

  function strictOk(tok, word) {
    const t = clean(tok);
    for (const lat in STRICT) if (count(t, lat) > count(word, STRICT[lat])) return false;
    for (const c of KZ) if (count(t, c) > count(word, c)) return false;
    return true;
  }

  const toLatin = text => Array.from(text).map(ch => (ch in LATIN ? LATIN[ch] : ch)).join("");

  // Character 5-gram model for unknown words (same as CharLM in src/restore.py: stupid back-off, beam search).
  const CYR_OPTS = {"а":"аә","г":"гғ","к":"кқ","н":"нң","о":"оө","у":"уұү","х":"хһ","и":"иі","ы":"ыі"};
  const CHAR_OPTS = {"a":"аә","k":"кқ","o":"оө","u":"уұү","i":"іиыйю","n":"нң","g":"гғ","h":"хһ","e":"еэ","j":"ж",
    "c":"цс","b":"б","v":"в","d":"д","z":"з","l":"л","m":"м","p":"п","r":"р","s":"с","t":"т","f":"ф","-":"-"};
  const STRICT_SKEL = {"q":"қ","ä":"ә","ö":"ө","ü":"ү","ğ":"ғ","ñ":"ң","ı":"ы","ş":"ш"};
  class CharLM {
    constructor(lines, n) {
      this.n = n; this.counts = new Map(); this.ctx = new Map();
      for (const line of lines) {
        const tab = line.lastIndexOf("\t");
        if (tab < 0) continue;
        const g = line.slice(0, tab), c = +line.slice(tab + 1);
        this.counts.set(g, c);
        const h = g.slice(0, -1);
        this.ctx.set(h, (this.ctx.get(h) || 0) + c);
      }
    }
    logp(history, ch) {
      let alpha = 0;
      for (let k = this.n - 1; k >= 0; k--) {
        const h = k ? history.slice(-k) : "";
        const c = this.counts.get(h + ch);
        if (c) return alpha + Math.log(c / this.ctx.get(h));
        alpha += Math.log(0.4);
      }
      return alpha + Math.log(1e-6);
    }
    restore(tok, beam = 16) {
      const t = clean(tok), slots = [];
      for (let i = 0; i < t.length;) {
        const two = t.slice(i, i + 2);
        if (["sh","zh","ch","gh"].includes(two)) { slots.push([{sh:"ш",zh:"ж",ch:"ч",gh:"ғ"}[two]]); i += 2; continue; }
        if (two === "yu" || two === "iu") { slots.push(["ю","иу","ыу","йу","іу"]); i += 2; continue; }
        if (two === "ya" || two === "ia") { slots.push(["я","иа","ыа","йа"]); i += 2; continue; }
        if (two === "ng") { slots.push(["ң","нг"]); i += 2; continue; }
        const ch = t[i];
        if (ch in CYR_OPTS) slots.push([...CYR_OPTS[ch]]);
        else if (ch in STRICT_SKEL) slots.push([STRICT_SKEL[ch]]);
        else if (ch === "y") slots.push(["ы","й","и"]);
        else if (ch === "w") slots.push(["ш","у"]);
        else if (ch === "x") slots.push(["х","һ"]);
        else if (ch in CHAR_OPTS) slots.push([...CHAR_OPTS[ch]]);
        else slots.push([ch]);
        i += 1;
      }
      const pad = "^".repeat(this.n - 1);
      let hyps = [[pad, 0]];
      for (const opts of slots) {
        const nxt = [];
        for (const [h, s] of hyps) for (const o of opts) {
          let sc = s, hh = h;
          for (const c of o) { sc += this.logp(hh, c); hh += c; }
          nxt.push([hh, sc]);
        }
        nxt.sort((a, b) => b[1] - a[1]);
        hyps = nxt.slice(0, beam);
      }
      let best = null;
      for (const [h, s] of hyps) { const sc = s + this.logp(h, "$"); if (!best || sc > best[1]) best = [h, sc]; }
      return best[0].slice(this.n - 1);
    }
  }

  class Engine {
    constructor(words, stats, bigrams, meta, russian, chars) {
      this.char = chars;
      this.words = words; this.meta = meta; this.russian = russian;
      this.id = new Map(words.map((w, i) => [w, i]));
      this.uni = new Uint32Array(words.length); this.ctx = new Uint32Array(words.length); this.fol = new Uint32Array(words.length);
      for (let i = 0; i < words.length; i++) { this.uni[i] = stats[3 * i]; this.ctx[i] = stats[3 * i + 1]; this.fol[i] = stats[3 * i + 2]; }
      this.big = bigrams;
      this.off = new Uint32Array(words.length + 1);
      const n = bigrams.length / 3;
      for (let k = 0; k < n; k++) this.off[bigrams[3 * k] + 1]++;
      for (let i = 1; i <= words.length; i++) this.off[i] += this.off[i - 1];
      this.byKey = new Map();
      for (let i = 2; i < words.length; i++) {
        const w = words[i];
        if (/^\d+$/.test(w)) continue;
        const k = canonWord(w);
        if (!this.byKey.has(k)) this.byKey.set(k, []);
        this.byKey.get(k).push(i);
      }
      for (const lst of this.byKey.values()) lst.sort((a, b) => this.uni[b] - this.uni[a]);
      this.denom = meta.total + 0.1 * (meta.vocab_full + 1);
    }
    u(w) { const i = this.id.get(w); return i === undefined ? 0 : this.uni[i]; }
    bigram(a, b) {
      let lo = this.off[a], hi = this.off[a + 1] - 1;
      const B = this.big;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1, v = B[3 * mid + 1];
        if (v === b) return B[3 * mid + 2];
        if (v < b) lo = mid + 1; else hi = mid - 1;
      }
      return 0;
    }
    logp(w, prev) {
      const pu = (this.u(w) + 0.1) / this.denom;
      const pi = this.id.get(prev);
      if (pi === undefined || this.ctx[pi] === 0) return Math.log(pu);
      const c = this.ctx[pi], t = this.fol[pi], lam = c / (c + t);
      const wi = this.id.get(w);
      const bc = wi === undefined ? 0 : this.bigram(pi, wi);
      return Math.log(lam * bc / c + (1 - lam) * pu);
    }
    candidates(tok, top = TOP) {
      const seen = new Map();
      for (const key of chatVariants(tok)) {
        const lst = this.byKey.get(key);
        if (!lst) continue;
        for (const i of lst.slice(0, top)) {
          const w = this.words[i];
          if (strictOk(tok, w)) seen.set(w, Math.max(seen.get(w) || 0, this.uni[i]));
        }
      }
      return [...seen.entries()].sort((a, b) => b[1] - a[1]).slice(0, top).map(e => e[0]);
    }
    fuzzyCandidates(tok, top = 10) {
      const found = new Map();
      for (const v of chatVariants(tok, 8)) {
        if (v.length < 4) continue;
        const keys = new Set();
        for (let i = 0; i < v.length; i++) keys.add(v.slice(0, i) + v.slice(i + 1));                 // extra letter typed
        for (let i = 0; i < v.length - 1; i++) keys.add(v.slice(0, i) + v[i + 1] + v[i] + v.slice(i + 2)); // swapped
        for (let i = 0; i <= v.length; i++) for (const c of SKEL) {
          keys.add(v.slice(0, i) + c + v.slice(i));                                                  // letter dropped
          if (i < v.length) keys.add(v.slice(0, i) + c + v.slice(i + 1));                            // wrong letter
        }
        keys.delete(v);
        for (const k of keys) {
          const lst = this.byKey.get(k);
          if (!lst || this.uni[lst[0]] < 3 || k.length < 3) continue;
          for (const i of lst.slice(0, 3)) {
            const w = this.words[i];
            if (strictOk(tok, w)) found.set(w, Math.max(found.get(w) || 0, this.uni[i]));
          }
        }
      }
      return [...found.entries()].sort((a, b) => b[1] - a[1]).slice(0, top).map(e => e[0]);
    }
    splitParticles(toks) {
      const out = [];
      for (const tok of toks) {
        const t = clean(tok);
        if (t.length >= 5 && PARTICLES.has(t.slice(-2))) {
          const whole = this.candidates(t, 1), wc = whole.length ? this.u(whole[0]) : 0;
          const stem = this.candidates(t.slice(0, -2), 1), sc = stem.length ? this.u(stem[0]) : 0;
          if (sc >= 20 && (wc === 0 || sc >= 200 * wc)) { out.push(t.slice(0, -2), t.slice(-2)); continue; }
        }
        out.push(tok);
      }
      return out;
    }
    isRussian(tok) {
      const t = clean(tok);
      if (!/^[а-яё-]+$/.test(t)) return false;
      if (/[щёъэ]/.test(t)) return true;
      if (!this.russian.has(t)) return false;
      const others = this.candidates(t, 5).filter(w => w !== t);
      return !others.length || this.u(others[0]) < 50;
    }
    channel(tok, word, habits) {
      if (!habits.size) return 0;
      const t = clean(tok);
      let pen = 0;
      for (const s of habits) {
        let typed = 0;
        for (const m of MARKERS[s]) typed += count(t, m);
        const extra = count(word, s) - typed;
        if (extra > 0) pen += HABIT * extra;
      }
      return pen;
    }
    lattice(text) {
      const toks = this.splitParticles(text.split(/\s+/).filter(Boolean));
      const low = text.toLowerCase();
      const habits = new Set(Object.keys(MARKERS).filter(s => [...MARKERS[s]].some(m => low.includes(m))));
      const lat = [];
      for (const tok of toks) {
        if (/^\d+$/.test(tok)) { lat.push([[tok, 0]]); continue; }
        if (this.isRussian(tok)) { lat.push([[clean(tok), 0]]); continue; }
        if (clean(tok) in CONTRACTIONS) { lat.push([[CONTRACTIONS[clean(tok)], 0]]); continue; }
        const cands = this.candidates(tok);
        const opts = cands.map(w => [w, this.channel(tok, w, habits)]);
        const best = cands.length ? this.u(cands[0]) : 0;
        if (tok.length >= 4 && best < FUZZY_BELOW) {
          const have = new Set(cands);
          const fz = this.fuzzyCandidates(tok).filter(w => !have.has(w));
          for (const w of fz) opts.push([w, TYPO + this.channel(tok, w, habits)]);
          if (fz.length && !cands.length) opts.push([this.guess(tok), 0]);
        }
        if (!opts.length) opts.push([this.guess(tok), OOV]);
        lat.push(opts);
      }
      return { toks, lat };
    }
    guess(tok) {   // unknown word: restore letter by letter with the character model
      return this.char ? this.char.restore(tok) : ruleWord(tok);
    }
    viterbi(lat) {
      let best = new Map([["<s>", [0, []]]]);
      for (const opts of lat) {
        const nxt = new Map();
        for (const [w, ch] of opts) {
          let cb = null;
          for (const [prev, [s, path]] of best) {
            const sc = s + ch + this.logp(w, prev);
            if (cb === null || sc > cb[0]) cb = [sc, path];
          }
          nxt.set(w, [cb[0], cb[1].concat([w])]);
        }
        best = nxt;
      }
      let fin = null;
      for (const [w, [s, path]] of best) { const sc = s + this.logp("</s>", w); if (fin === null || sc > fin[0]) fin = [sc, path]; }
      return fin[1];
    }
    restore(text) {
      const { lat } = this.lattice(text);
      return lat.length ? this.viterbi(lat).join(" ") : "";
    }
    restoreWithConfidence(text, topK = 3) {
      const { toks, lat } = this.lattice(text);
      if (!lat.length) return [];
      const words = this.viterbi(lat);
      const fwd = [new Map([["<s>", 0]])];
      for (const opts of lat) {
        const cur = new Map(), prevs = [...fwd[fwd.length - 1].entries()];
        for (const [w, ch] of opts) cur.set(w, ch + lse(prevs.map(([p, s]) => s + this.logp(w, p))));
        fwd.push(cur);
      }
      const z = lse([...fwd[fwd.length - 1].entries()].map(([w, s]) => s + this.logp("</s>", w)));
      const bwd = new Array(lat.length);
      bwd[lat.length - 1] = new Map(lat[lat.length - 1].map(([w]) => [w, this.logp("</s>", w)]));
      for (let i = lat.length - 2; i >= 0; i--) {
        const nxt = lat[i + 1], m = new Map();
        for (const [w] of lat[i]) m.set(w, lse(nxt.map(([v, ch]) => ch + this.logp(v, w) + bwd[i + 1].get(v))));
        bwd[i] = m;
      }
      return toks.map((tok, i) => {
        const post = lat[i].map(([v]) => [v, Math.exp(fwd[i + 1].get(v) + bwd[i].get(v) - z)]);
        post.sort((a, b) => b[1] - a[1]);
        const conf = (post.find(p => p[0] === words[i]) || [0, 0])[1];
        return { typed: tok, word: words[i], confidence: conf, alternatives: post.slice(0, topK) };
      });
    }
  }

  async function load(base, fetchFn) {
    const get = async (name, kind) => {
      const r = await fetchFn(base + name);
      if (!r.ok) throw new Error("could not load " + name);
      return kind === "bin" ? r.arrayBuffer() : r.text();
    };
    const [wordsTxt, statsBuf, bigBuf, metaTxt, ruTxt, charTxt] = await Promise.all([
      get("words.txt"), get("stats.bin", "bin"), get("bigrams.bin", "bin"), get("meta.json"), get("ru.txt"), get("chars.txt")]);
    const meta = JSON.parse(metaTxt);
    return new Engine(wordsTxt.split(/\r?\n/), new Uint32Array(statsBuf), new Uint32Array(bigBuf), meta,
      new Set(ruTxt.split(/\r?\n/).map(l => l.trim().split(/\s+/)[0]).filter(Boolean)),
      new CharLM(charTxt.split(/\r?\n/), meta.char_order || 5));
  }

  const api = { load, Engine, ruleWord, toLatin, chatVariants };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.Qalaisyn = api;
})(typeof self !== "undefined" ? self : this);
