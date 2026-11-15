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
      host.style.cssText = "position:fixed;right:28px;bottom:120px;z-index:2147483647";
      const sh = host.attachShadow({ mode: "open" });
      sh.innerHTML = `<style>
        .b{font:16px/1.5 "Segoe UI",system-ui,sans-serif;background:#fff;color:#1A1F24;border:1px solid #D9DEE3;
           border-top:4px solid #0B7A80;border-radius:10px;padding:12px 18px 14px;width:max-content;max-width:560px;
           box-shadow:0 14px 36px rgba(16,24,32,.16)}
        .h{display:flex;align-items:center;gap:9px;font-size:14px;color:#4F5A64;padding-bottom:10px;margin-bottom:10px;border-bottom:1px solid #EEF1F3}
        .h b{color:#0B7A80;font-weight:700;font-size:16px}
        .q{width:22px;height:22px;border-radius:6px;background:#0B7A80;color:#fff;font:700 14px/22px "Segoe UI",sans-serif;text-align:center}
        .h .ms{margin-left:auto;color:#7A848D;padding-left:22px}
        .row{display:grid;grid-template-columns:76px 1fr;gap:12px;align-items:baseline}
        .row+.row{margin-top:5px}
        .lbl{font-size:13px;color:#8A939B}
        .was{color:#7A848D;font-size:16px} .now{color:#1A1F24;font-size:18px}
        u{text-decoration:none;background:#BFE7E3;color:#04484C;font-weight:700;border-radius:3px;padding:0 1px}</style>
        <div class="b"></div>`;
      box = sh.querySelector(".b");
      document.documentElement.appendChild(host);
    }
    box.innerHTML = html;
    host.style.display = "block";
    clearTimeout(timer);
    if (ms) timer = setTimeout(() => { host.style.display = "none"; }, ms);
  }

  const head = (title = "", right = "") =>
    `<div class="h"><span class="q">Q</span><b>Qalaisyn</b><span>${title}</span><span class="ms">${right}</span></div>`;
  const esc = s => s.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  function diffHtml(a, b) {          // underline only the letters Qalaisyn put back
    const pa = a.split(/(\s+)/), pb = b.split(/(\s+)/);
    if (pa.length !== pb.length) return esc(b);
    return pb.map((w, i) => {
      const o = pa[i];
      if (w === o) return esc(w);
      if (w.length !== o.length) return `<u>${esc(w)}</u>`;
      return [...w].map((ch, k) => (ch !== o[k] ? `<u>${esc(ch)}</u>` : esc(ch))).join("");
    }).join("");
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
    if (!t) { toast(head() + 'Click into a text field first, then press Alt+Q.'); return; }
    let eng;
    try {
      if (!enginePromise) toast(head() + 'Loading the engine (once per page)…', 0);
      eng = await engine();
    } catch (e) { toast(head() + 'Could not load the engine: ' + esc(String(e))); return; }

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
      ? head() + "Nothing to fix here."
      : head(`put back ${n} Kazakh letter${n === 1 ? "" : "s"}`, `${ms} ms`) +
        `<div class="row"><span class="lbl">Typed</span><span class="was">${esc(before)}</span></div>` +
        `<div class="row"><span class="lbl">Restored</span><span class="now">${diffHtml(before, after)}</span></div>`, 6500);
  }

  document.addEventListener("keydown", e => {
    if (e.altKey && !e.ctrlKey && !e.metaKey && (e.code === "KeyQ")) { e.preventDefault(); e.stopPropagation(); run(); }
  }, true);
  chrome.runtime.onMessage.addListener(m => { if (m && m.qalaisyn === "run") run(); });
})();
