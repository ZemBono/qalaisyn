// Qalaisyn for Chrome: press Alt+Q in any text field (or click the toolbar icon) and the
// Kazakh letters dropped on a Russian keyboard or in Latin are put back, right in that field.
(() => {
  if (window.__qalaisynLoaded) return;
  window.__qalaisynLoaded = true;

  let enginePromise = null;
  const engine = () => enginePromise ||= Qalaisyn.load(chrome.runtime.getURL("model/"), fetch);

  const WORD = /([A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі'-]+)/;
  const strip = s => s.toLowerCase().replace(/[^a-zа-яёәғқңөұүһі]/g, "");

  function matchCase(orig, out) {
    if (orig.length > 1 && orig === orig.toUpperCase() && orig !== orig.toLowerCase()) return out.toUpperCase();
    if (orig[0] && orig[0] !== orig[0].toLowerCase()) return out[0].toUpperCase() + out.slice(1);
    return out;
  }

  // Restore a sentence and map the result back onto the original words, keeping punctuation and case.
  function restoreSentence(eng, words) {
    const low = words.map(w => w.toLowerCase());
    const res = eng.restoreWithConfidence(low.join(" "));
    const out = [];
    let j = 0;
    for (let i = 0; i < words.length; i++) {
      const target = strip(low[i]);
      let typed = "", parts = [];
      while (j < res.length && typed.length < target.length) { typed += strip(res[j].typed); parts.push(res[j].word); j++; }
      out.push(typed === target && parts.length ? matchCase(words[i], parts.join(" ")) : words[i]);
    }
    return out;
  }

  function restoreText(eng, text) {
    const pieces = text.split(WORD);            // even = separators, odd = words
    let sentence = [];
    const flush = () => {
      if (!sentence.length) return;
      const fixed = restoreSentence(eng, sentence.map(i => pieces[i]));
      sentence.forEach((idx, k) => { pieces[idx] = fixed[k]; });
      sentence = [];
    };
    for (let i = 0; i < pieces.length; i++) {
      if (i % 2) { if (/^[-']+$/.test(pieces[i])) continue; sentence.push(i); }
      else if (/[.!?\n]/.test(pieces[i])) flush();
    }
    flush();
    return pieces.join("");
  }

  function countChanged(a, b) {
    const k = "әғқңөұүһі";
    let n = 0;
    for (const ch of b.toLowerCase()) if (k.includes(ch)) n++;
    for (const ch of a.toLowerCase()) if (k.includes(ch)) n--;
    return Math.max(n, 0);
  }

  // ---- small notice in the corner (shadow DOM, so the page's styles don't touch it)
  let host, box, timer;
  function toast(html, ms = 4000) {
    if (!host) {
      host = document.createElement("div");
      host.style.cssText = "position:fixed;right:20px;bottom:20px;z-index:2147483647";
      const sh = host.attachShadow({ mode: "open" });
      sh.innerHTML = `<style>
        .b{font:14px/1.45 system-ui,Segoe UI,sans-serif;background:#16303A;color:#EAF2F4;border-radius:14px;
           padding:12px 16px;max-width:420px;box-shadow:0 8px 30px rgba(0,0,0,.25)}
        .t{font-weight:700;color:#7FD6DC;margin-bottom:2px} .w{opacity:.8} b{color:#FFD27A;font-weight:600}</style>
        <div class="b"></div>`;
      box = sh.querySelector(".b");
      document.documentElement.appendChild(host);
    }
    box.innerHTML = html;
    host.style.display = "block";
    clearTimeout(timer);
    if (ms) timer = setTimeout(() => { host.style.display = "none"; }, ms);
  }

  const esc = s => s.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  function diffHtml(a, b) {
    const pa = a.split(/(\s+)/), pb = b.split(/(\s+)/);
    if (pa.length !== pb.length) return esc(b);
    return pb.map((w, i) => (w !== pa[i] ? `<b>${esc(w)}</b>` : esc(w))).join("");
  }

  // ---- reading and writing the focused field
  function target() {
    let el = document.activeElement;
    while (el && el.shadowRoot && el.shadowRoot.activeElement) el = el.shadowRoot.activeElement;
    if (!el) return null;
    if (el.tagName === "TEXTAREA" || (el.tagName === "INPUT" && /^(text|search|)$/i.test(el.type))) return { el, kind: "input" };
    const ce = el.isContentEditable ? el.closest('[contenteditable="true"],[contenteditable=""]') || el : null;
    return ce ? { el: ce, kind: "editable" } : null;
  }

  function setInputValue(el, value) {
    const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value").set.call(el, value);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  async function run() {
    const t = target();
    if (!t) { toast('<div class="t">Qalaisyn</div>Click into a text field first, then press <b>Alt+Q</b>.'); return; }
    let eng;
    try {
      if (!enginePromise) toast('<div class="t">Qalaisyn</div>Loading the engine (once per page)…', 0);
      eng = await engine();
    } catch (e) { toast('<div class="t">Qalaisyn</div>Could not load the engine: ' + esc(String(e))); return; }

    const t0 = performance.now();
    let before, after;
    if (t.kind === "input") {
      const el = t.el, s = el.selectionStart ?? 0, e = el.selectionEnd ?? 0;
      const whole = el.value, part = e > s;
      before = part ? whole.slice(s, e) : whole;
      after = restoreText(eng, before);
      if (after !== before) {
        setInputValue(el, part ? whole.slice(0, s) + after + whole.slice(e) : after);
        const end = part ? s + after.length : after.length;
        try { el.setSelectionRange(end, end); } catch (_) {}
      }
    } else {
      const el = t.el, sel = getSelection();
      const part = sel.rangeCount && !sel.isCollapsed && el.contains(sel.anchorNode);
      before = part ? sel.toString() : el.innerText.replace(/\n$/, "");
      after = restoreText(eng, before);
      if (after !== before) {
        if (!part) { const r = document.createRange(); r.selectNodeContents(el); sel.removeAllRanges(); sel.addRange(r); }
        document.execCommand("insertText", false, after);
      }
    }
    const ms = (performance.now() - t0).toFixed(1), n = countChanged(before, after);
    toast(after === before
      ? '<div class="t">Qalaisyn</div>Nothing to fix here.'
      : `<div class="t">Qalaisyn put back ${n} Kazakh letter${n === 1 ? "" : "s"} · ${ms} ms</div>` +
        `<div class="w">${esc(before)}</div><div>${diffHtml(before, after)}</div>`, 6000);
  }

  document.addEventListener("keydown", e => {
    if (e.altKey && !e.ctrlKey && !e.metaKey && (e.code === "KeyQ")) { e.preventDefault(); e.stopPropagation(); run(); }
  }, true);
  chrome.runtime.onMessage.addListener(m => { if (m && m.qalaisyn === "run") run(); });
})();
