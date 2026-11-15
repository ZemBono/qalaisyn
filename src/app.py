"""Qalaisyn demo: type Kazakh the way people really text and see what an AI understands, before and after."""
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
THRESHOLD = 0.9   # chosen on FLORES dev (src/confidence.py)

EXAMPLES_RU = [
    "баламнын кызуы 39 котерилди не истеу керек",
    "салем калайсын ертен мектепке барасын ба",
    "ажеме жедел жардем керек уйге келиниз",
    "картадан акша шешилип кетипти мен ешнарсе алмадым",
]
EXAMPLES_LAT = [
    "balamnyn qyzuy 39 koterildi ne isteu kerek",
    "salem qalaisyn erteng mektepke barasyn ba",
    "raxmet bauyrym komektesken ushin",
]

# Everyday places where a misread message costs something. Outputs are computed live at start-up.
USE_CASES = [
    ("Bank support chat", "A customer cannot pay a loan and asks for help.",
     "кредит толей алмай журмин комектесиниздер", "The bot offers payment options instead of a confused reply."),
    ("Clinic chatbot", "A parent writes at night about a child with a fever.",
     "баламнын кызуы 39 котерилди не истеу керек", "The message is treated as urgent, not as noise."),
    ("E-government (eGov)", "Someone lost their ID card and asks what to do.",
     "жеке куалигимди жогалтып алдым не истеу керек", "They get the right instructions instead of a wrong answer."),
    ("Airline support", "A passenger asks if the flight is delayed.",
     "ушак кешигип жатыр ма", "The passenger gets flight status instead of nonsense."),
]

CSS = """
:root, .gradio-container {
  --paper:#F4F6F8; --card:#FFFFFF; --ink:#1B2433; --muted:#5F6B7A; --line:#DCE1E7;
  --gold:#E3A72F; --gold-soft:#FBEFD2; --brick:#A8513B; --brick-soft:#F7E9E4; --sea:#1F6F78; --sea-soft:#E3F1F1;
}
body, gradio-app {background:#F4F6F8!important}
.gradio-container {background:var(--paper)!important; max-width:1120px!important; margin:0 auto!important;
  font-family:'Golos Text', 'Segoe UI', sans-serif!important; color:var(--ink)}
footer {display:none!important}
#hero h1 {font-size:40px; line-height:1.12; letter-spacing:-.02em; font-weight:700; margin:8px 0 10px; max-width:820px}
#hero p {font-size:18px; line-height:1.55; color:var(--muted); max-width:720px; margin:0}
#hero .brand {font-weight:700; font-size:17px; color:var(--sea); letter-spacing:.01em}
#hero .brand b {color:var(--gold)}
#panel {background:var(--card); border:1px solid var(--line); border-radius:18px; padding:22px; margin-top:18px}
#msg textarea {font-size:21px!important; line-height:1.45!important; background:#E9F3F2!important;
  border:1px solid #CFE3E1!important; border-radius:18px 18px 18px 6px!important; padding:14px 16px!important; color:var(--ink)!important}
#msg label span {font-size:14px!important; color:var(--muted)!important; font-weight:500!important}
#go {background:var(--sea)!important; color:white!important; font-size:17px!important; border-radius:12px!important;
  border:none!important; min-height:52px}
#go:hover {background:#18595F!important}
.exlabel {font-size:14px; color:var(--muted); margin:14px 0 4px}
button.exbtn {background:white!important; border:1px solid var(--line)!important; border-radius:999px!important;
  font-size:15px!important; color:#1B2433!important; font-weight:400!important; padding:6px 14px!important;
  justify-content:flex-start!important; box-shadow:none!important; min-height:0!important; width:auto!important}
button.exbtn:hover {border-color:#1F6F78!important; color:#1F6F78!important}
.exrow {gap:8px!important; flex-wrap:wrap!important}
.res {display:grid; gap:12px}
.box {border-radius:14px; padding:14px 18px; border:1px solid var(--line); background:white}
.box .k {font-size:14px; color:var(--muted); margin-bottom:6px}
.box .v {font-size:22px; line-height:1.45}
.box.before {background:var(--brick-soft); border-color:#EBCFC6}
.box.before .v {color:var(--brick)}
.box.after {background:var(--sea-soft); border-color:#C4E0E0}
.box.after .v {color:#164E54; font-weight:500}
.box.fixed .v {font-size:24px}
.lt {background:var(--gold-soft); box-shadow:inset 0 -3px 0 var(--gold); border-radius:3px; padding:0 1px}
.unsure {text-decoration:underline dotted #B7791F 2px; text-underline-offset:6px}
.sugg {margin-top:12px; font-size:15px; color:var(--muted)}
.chip {display:inline-block; margin:6px 6px 0 0; padding:4px 12px; border-radius:999px; background:#FFFBF1;
  border:1px solid #F0D9A6; color:var(--ink)}
.chip b {font-weight:600}
.empty {color:var(--muted); font-size:17px; padding:30px 6px}
#how {margin-top:26px}
#how h2 {font-size:22px; margin:0 0 12px; font-weight:700}
.steps {display:grid; grid-template-columns:repeat(3,1fr); gap:14px}
.step {background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px}
.step .n {display:inline-flex; width:28px; height:28px; border-radius:50%; background:var(--sea); color:white;
  align-items:center; justify-content:center; font-weight:700; font-size:15px; margin-bottom:8px}
.step h3 {font-size:17px; margin:0 0 6px}
.step p {font-size:15px; line-height:1.5; color:var(--muted); margin:0}
.step code {background:var(--paper); padding:1px 5px; border-radius:5px; font-size:14px; color:var(--ink)}
.where {margin-top:16px; display:flex; flex-wrap:wrap; gap:8px; align-items:center; font-size:15px; color:var(--muted)}
.where span.p {background:white; border:1px solid var(--line); border-radius:999px; padding:4px 12px; color:var(--ink)}
.facts {margin-top:22px; display:grid; grid-template-columns:repeat(3,1fr); gap:14px}
.fact {border-top:3px solid var(--sea); padding-top:10px}
.fact .big {font-size:30px; font-weight:700; letter-spacing:-.01em}
.fact p {font-size:14px; color:var(--muted); margin:2px 0 0; line-height:1.45}
#uses {margin-top:30px}
#uses h2 {font-size:22px; margin:0 0 6px; font-weight:700}
#uses .lead {font-size:16px; color:var(--muted); margin:0 0 14px; max-width:760px; line-height:1.5}
.ucs {display:grid; grid-template-columns:repeat(2,1fr); gap:14px}
.uc {background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px}
.uc h3 {font-size:17px; margin:0 0 2px}
.uc .sit {font-size:14px; color:var(--muted); margin:0 0 10px}
.bubble {display:inline-block; background:#E9F3F2; border:1px solid #CFE3E1; border-radius:14px 14px 14px 4px;
  padding:8px 12px; font-size:16px; margin-bottom:10px}
.ucrow {font-size:15px; line-height:1.45; padding:6px 0; border-top:1px solid var(--line)}
.ucrow span {display:block; font-size:12.5px; color:var(--muted)}
.ucrow.bad {color:var(--brick)}
.ucrow.good {color:#164E54; font-weight:500}
.uc .out {font-size:14px; margin:8px 0 0; color:var(--ink)}
@media (max-width:760px){ .ucs{grid-template-columns:1fr} }
.note {font-size:13px; color:var(--muted); margin:22px 0 8px}
@media (max-width:760px){ #hero h1{font-size:30px} .steps,.facts{grid-template-columns:1fr} }
"""

HERO = """
<div id="hero">
  <div class="brand">Qalaisyn<b>.</b></div>
  <h1>People type Kazakh the way their phone allows. Qalaisyn makes AI understand it.</h1>
  <p>Most phones in Kazakhstan have a Russian keyboard, so <i>қалайсың</i> becomes <i>калайсын</i> and
  chatbots and translators lose the meaning. Type a message the way people really text and compare what
  the AI understands before and after.</p>
</div>
"""

HOW = """
<div id="how">
  <h2>How it works</h2>
  <div class="steps">
    <div class="step"><div class="n">1</div><h3>List the possible words</h3>
      <p>Each typed word could be several Kazakh words: <code>кызуы</code> → қызуы or кызуы,
      <code>н</code> → н or ң. Qalaisyn lists the real words it could be.</p></div>
    <div class="step"><div class="n">2</div><h3>Pick the most likely sentence</h3>
      <p>A language model trained on 1.5 million Kazakh sentences scores how words fit together, and the
      Viterbi algorithm picks the best whole sentence.</p></div>
    <div class="step"><div class="n">3</div><h3>Ask only when unsure</h3>
      <p>Every word gets a probability. Below 90% it is shown as a suggestion instead of being changed
      silently, about 1 word in 20.</p></div>
  </div>
  <div class="where">Not an app to download. A layer inside:
    <span class="p">bank support chats</span><span class="p">clinic chatbots</span>
    <span class="p">e-government</span><span class="p">translators</span><span class="p">phone keyboards</span></div>
  <div class="facts">
    <div class="fact"><div class="big">47% → 3.6%</div><p>words misspelled on a Russian keyboard, before and after Qalaisyn (held-out test set)</p></div>
    <div class="fact"><div class="big">87%</div><p>of lost meaning recovered on messy messages with typos; a dictionary lookup recovers 67%</p></div>
    <div class="fact"><div class="big">59%</div><p>of Qalaisyn's own mistakes are among the 5% of words it marks as unsure</p></div>
  </div>
  <p class="note">Prototype for the Veritas AI High School Hackathon 2026, Languages track. Translator used for the
  comparison: NLLB-200 (Meta). Not for medical or emergency use.</p>
</div>
"""

def use_cases_html():
    msgs = [m for _, _, m, _ in USE_CASES]
    fixed = [QAL.restore(m) for m in msgs]
    tr = TR.translate(msgs + fixed)
    before, after = tr[:len(msgs)], tr[len(msgs):]
    cards = []
    for (place, situation, msg, outcome), f, b, a in zip(USE_CASES, fixed, before, after):
        cards.append(
            f"<div class='uc'><h3>{place}</h3><p class='sit'>{situation}</p>"
            f"<div class='bubble'>{html.escape(msg)}</div>"
            f"<div class='ucrow bad'><span>AI without Qalaisyn</span>{html.escape(b)}</div>"
            f"<div class='ucrow good'><span>AI with Qalaisyn</span>{html.escape(a)}</div>"
            f"<p class='out'>{outcome}</p></div>")
    return ("<div id='uses'><h2>Where it helps every day</h2>"
            "<p class='lead'>Over 13 million people speak Kazakh, and support chats, clinics and government services "
            "are moving to AI first. A message the AI misreads means a wrong answer, a lost customer or a delayed emergency. "
            "These are live results from the same model, not mock-ups.</p>"
            f"<div class='ucs'>{''.join(cards)}</div></div>")


USES = use_cases_html()

EMPTY = "<div class='empty'>Type a message on the left, or pick an example, and press <b>Restore and translate</b>.</div>"


def highlight(naive: str, restored: str) -> str:
    """Wrap the letters Qalaisyn decided (different from a naive letter-by-letter reading)."""
    out = []
    for op, _, _, b0, b1 in difflib.SequenceMatcher(a=naive, b=restored).get_opcodes():
        seg = html.escape(restored[b0:b1])
        out.append(seg if op == "equal" else f"<span class='lt'>{seg}</span>")
    return "".join(out)


def run(msg):
    msg = " ".join(re.findall(r"[\w'-]+", (msg or "").strip().lower()))
    if not msg:
        return EMPTY
    words = QAL.restore_with_confidence(msg)
    restored = " ".join(w["word"] for w in words)
    before, after = TR.translate([msg, restored])
    shown, sugg = [], []
    for w in words:
        seg = highlight(RULES.restore(w["typed"]), w["word"])
        if w["confidence"] < THRESHOLD:
            seg = f"<span class='unsure'>{seg}</span>"
            alts = " · ".join(f"<b>{html.escape(a)}</b> {p:.0%}" if a == w["word"] else f"{html.escape(a)} {p:.0%}"
                              for a, p in w["alternatives"] if p >= 0.03)
            sugg.append(f"<span class='chip'>{alts}</span>")
        shown.append(seg)
    fixed = " ".join(shown)
    if sugg:
        fixed += "<div class='sugg'>Not sure, so the user sees a suggestion:<br>" + "".join(sugg) + "</div>"
    return ("<div class='res'>"
            f"<div class='box before'><div class='k'>What the AI understands from the message as typed</div>"
            f"<div class='v'>{html.escape(before)}</div></div>"
            f"<div class='box fixed'><div class='k'>Qalaisyn restores the Kazakh letters (highlighted)</div>"
            f"<div class='v'>{fixed}</div></div>"
            f"<div class='box after'><div class='k'>What the AI understands after Qalaisyn</div>"
            f"<div class='v'>{html.escape(after)}</div></div>"
            "</div>")


theme = gr.themes.Base(font=[gr.themes.GoogleFont("Golos Text"), "Segoe UI", "sans-serif"])
with gr.Blocks(title="Qalaisyn", css=CSS, theme=theme) as demo:
    gr.HTML(HERO)
    with gr.Row(elem_id="panel", equal_height=False):
        with gr.Column(scale=5):
            inp = gr.Textbox(label="A message, typed like in a chat", value=EXAMPLES_RU[0], lines=3, elem_id="msg")
            btn = gr.Button("Restore and translate", elem_id="go")
            gr.HTML("<div class='exlabel'>Try an example typed on a Russian keyboard</div>")
            with gr.Column(elem_classes="exrow"):
                ex_ru = [gr.Button(e, elem_classes="exbtn", size="sm", variant="secondary") for e in EXAMPLES_RU]
            gr.HTML("<div class='exlabel'>or in Latin letters</div>")
            with gr.Column(elem_classes="exrow"):
                ex_lat = [gr.Button(e, elem_classes="exbtn", size="sm", variant="secondary") for e in EXAMPLES_LAT]
        with gr.Column(scale=6):
            out = gr.HTML(EMPTY)
    gr.HTML(USES)
    gr.HTML(HOW)
    btn.click(run, inp, out)
    inp.submit(run, inp, out)
    for b, text in zip(ex_ru + ex_lat, EXAMPLES_RU + EXAMPLES_LAT):
        b.click(lambda t=text: t, None, inp).then(run, inp, out)
    demo.load(run, inp, out)

if __name__ == "__main__":
    demo.launch(share="--share" in sys.argv)
