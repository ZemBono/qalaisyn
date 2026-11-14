"""Qalaisyn demo: type Kazakh the way you text, see what AI understands before and after."""
import difflib
import html
import re
import sys
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).parent))
from eval_restore import load_lexicon  # noqa: E402
from eval_translate import Translator  # noqa: E402
from restore import QalaisynRestorer, RuleRestorer  # noqa: E402

LEX = load_lexicon()
QAL = QalaisynRestorer(LEX, fuzzy=True)
RULES = RuleRestorer()
TR = Translator()

EXAMPLES = [
    "баламнын кызуы 39 котерилди не истеу керек",
    "салем калайсын ертен мектепке барасын ба",
    "ажеме жедел жардем керек уйге келиниз",
    "balamnyn qyzuy 39 koterildi ne isteu kerek",
    "erekshe atap ot",
    "raxmet bauyrym komektesken ushin",
]
THRESHOLD = 0.9   # chosen on FLORES dev (src/confidence.py)

CSS = """
.card {border-radius:14px;padding:16px 18px;margin:8px 0;border:1px solid}
.card h4 {margin:0 0 6px;font-size:13px;letter-spacing:.04em;text-transform:uppercase;opacity:.75}
.card p {margin:0;font-size:21px;line-height:1.45}
.bad  {background:#fdecea;border-color:#f5c2bb;color:#7a1f12}
.mid  {background:#fff8e1;border-color:#f3dc8b;color:#4a3b00}
.good {background:#e6f6f0;border-color:#a7dcc8;color:#0b4a37}
mark {background:#ffd34d;border-radius:4px;padding:0 1px}
.unsure {border-bottom:3px dotted #c2410c}
.sugg {margin-top:10px;font-size:15px;line-height:1.9}
.chip {display:inline-block;border:1px solid #e5c76b;background:#fffdf3;border-radius:999px;padding:1px 10px;margin:0 4px}
.chip b {color:#0b4a37}
.arrow {text-align:center;font-size:20px;opacity:.5;margin:-2px 0}
"""


def highlight(naive: str, restored: str) -> str:
    """Mark the letters Qalaisyn chose differently from a naive letter-by-letter reading."""
    out = []
    for op, _, _, b0, b1 in difflib.SequenceMatcher(a=naive, b=restored).get_opcodes():
        seg = html.escape(restored[b0:b1])
        out.append(seg if op == "equal" else f"<mark>{seg}</mark>")
    return "".join(out)


def card(cls, title, body):
    return f"<div class='card {cls}'><h4>{title}</h4><p>{body}</p></div>"


def run(msg):
    msg = " ".join(re.findall(r"[\w'-]+", msg.strip().lower()))   # punctuation is ignored
    if not msg:
        return ""
    words = QAL.restore_with_confidence(msg)
    restored = " ".join(w["word"] for w in words)
    before, after = TR.translate([msg, restored])
    shown, sugg = [], []
    for w in words:
        seg = highlight(RULES.restore(w["typed"]), w["word"])
        if w["confidence"] < THRESHOLD:
            seg = f"<span class='unsure' title='Qalaisyn is not sure'>{seg}</span>"
            alts = " · ".join(f"<b>{html.escape(a)}</b> {p:.0%}" if a == w["word"] else f"{html.escape(a)} {p:.0%}"
                              for a, p in w["alternatives"] if p >= 0.03)
            sugg.append(f"<span class='chip'>{html.escape(w['typed'])} → {alts}</span>")
        shown.append(seg)
    body = " ".join(shown)
    if sugg:
        body += ("<div class='sugg'>Not sure — suggestions the user can tap: " + "".join(sugg) + "</div>")
    return (card("bad", "1 · AI reads the message as typed", html.escape(before))
            + "<div class='arrow'>↓ Qalaisyn restores the Kazakh letters</div>"
            + card("mid", "2 · Restored Kazakh (yellow = letters Qalaisyn decided, dotted = not sure)", body)
            + "<div class='arrow'>↓</div>"
            + card("good", "3 · AI reads the restored message", html.escape(after)))


with gr.Blocks(title="Qalaisyn", css=CSS, theme=gr.themes.Soft(primary_hue="emerald", font=[gr.themes.GoogleFont("Inter"), "Segoe UI", "sans-serif"])) as demo:
    gr.Markdown(
        "# Qalaisyn\n"
        "**AI understands Kazakh only when it's written 'properly' — and almost nobody texts that way.**  \n"
        "Type a Kazakh message the way people really text: on a Russian keyboard (*калайсын*) or in Latin "
        "(*qalaisyn*), without the special Kazakh letters.")
    with gr.Row():
        inp = gr.Textbox(label="Chat-style Kazakh message", value=EXAMPLES[0], scale=5)
        btn = gr.Button("Translate", variant="primary", scale=1)
    out = gr.HTML()
    gr.Examples(EXAMPLES, inp)
    btn.click(run, inp, out)
    inp.submit(run, inp, out)
    demo.load(run, inp, out)
    gr.Markdown("_Prototype · Veritas AI High School Hackathon 2026 · translator: NLLB-200 (Meta) · not for medical or emergency use._")

if __name__ == "__main__":
    demo.launch(share="--share" in sys.argv)
