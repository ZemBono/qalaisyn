"""Qalaisyn demo.
Qalaisyn is an engine that sits *inside* other systems (support chatbots, translators,
search). This page is only a window into it: (1) a support chatbot with and without Qalaisyn inside,
(2) a look inside the engine for any message."""
import difflib
import html
import re
import sys
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).parent))
from eval_restore import load_lexicon  # noqa: E402
from eval_translate import Translator  # noqa: E402
from latin import to_latin  # noqa: E402
from restore import QalaisynRestorer, RuleRestorer  # noqa: E402

LEX = load_lexicon()
QAL = QalaisynRestorer(LEX, fuzzy=True)
RULES = RuleRestorer()
TR = Translator()
THRESHOLD = 0.9   # chosen on FLORES dev (src/confidence.py)

# ------------------------------------------------------------------ toy support bot
# A deliberately simple bot: keyword rules on the English translation of the customer's message,
# like many first-line support bots. Only for showing what Qalaisyn changes; not part of the model.
INTENTS = [
    (["delay payment", "delay my payment", "postpone", "can't pay", "can 't pay", "cannot pay"],
     "I can move your loan payment date by up to 30 days at no cost. Shall I do it?"),
    (["cash out", "withdraw"], "To withdraw cash from your loan account, visit any of our ATMs with your card."),
    (["my money", "money back", "refund"], "Sorry about the missing order. Your refund is on its way: 3–5 working days."),
    (["return the order", "return an order"], "To return an order, pack the item and book a courier pickup in the app."),
    (["plane", "flight", "aircraft"], "Flight KC 852 to Astana is delayed by 40 minutes. New departure: 18:40."),
    (["lost my id", "lost id", "id card", "identity card", "lost my passport"],
     "You can order a new ID card on eGov: Services → Documents → Lost ID. It takes about 10 days."),
    (["credential", "password", "login"], "To reset your password, open Settings → Security → Reset password."),
]
FALLBACK = "Sorry, I did not understand your question. A human operator will reply in about 25 minutes."


def bot_reply(english: str) -> str:
    e = english.lower()
    for keys, answer in INTENTS:
        if any(k in e for k in keys):
            return answer
    return FALLBACK


SCENARIOS = [
    ("Bank: delay a loan payment", "несие бойынша толемди кешиктирсем бола ма"),
    ("Airline: is my flight late?", "ушак кешигип жатыр ма"),
    ("E-government: lost ID card", "жеке куалигимди жогалтып алдым не истеу керек"),
]
EXAMPLES_RU = [
    "баламнын кызуы 39 котерилди не истеу керек",
    "салем калайсын ертен мектепке барасын ба",
    "кредит толей алмай журмин комектесиниздер",
]
EXAMPLES_LAT = [
    "balamnyn qyzuy 39 koterildi ne isteu kerek",
    "salem qalaisyn erteng mektepke barasyn ba",
]
EN_FUNCTION_WORDS = set("the a an and or is are am was to of in on for my your you i it this that what how hello hi "
                        "with be do does can not no yes please thanks thank site restaurant".split())


def clean(msg: str) -> str:
    return " ".join(re.findall(r"[\w'-]+", (msg or "").strip().lower()))


def looks_english(msg: str) -> bool:
    toks = msg.split()
    if not toks or re.search(r"[а-яәғқңөұүһі]", msg):
        return False
    return sum(t in EN_FUNCTION_WORDS for t in toks) / len(toks) >= 0.34


def highlight(naive: str, restored: str) -> str:
    out = []
    for op, _, _, b0, b1 in difflib.SequenceMatcher(a=naive, b=restored).get_opcodes():
        seg = html.escape(restored[b0:b1])
        out.append(seg if op == "equal" else f"<span class='lt'>{seg}</span>")
    return "".join(out)


def restored_html(words):
    shown, sugg = [], []
    for w in words:
        seg = highlight(RULES.restore(w["typed"]), w["word"])
        if w["confidence"] < THRESHOLD:
            seg = f"<span class='unsure'>{seg}</span>"
            alts = " · ".join(f"<b>{html.escape(a)}</b> {p:.0%}" if a == w["word"] else f"{html.escape(a)} {p:.0%}"
                              for a, p in w["alternatives"] if p >= 0.03)
            sugg.append(f"<span class='chip'>{alts}</span>")
        shown.append(seg)
    body = " ".join(shown)
    if sugg:
        body += "<div class='sugg'>Not sure, so this becomes a suggestion: " + "".join(sugg) + "</div>"
    return body


NOT_KAZAKH = ("<div class='empty'>This does not look like Kazakh. Qalaisyn only changes Kazakh words, so an "
              "English message is passed through unchanged.</div>")


# ------------------------------------------------------------------ chatbot view
def chat(msg):
    msg = clean(msg)
    if not msg:
        return "", "", ""
    if looks_english(msg):
        return NOT_KAZAKH, "", ""
    words = QAL.restore_with_confidence(msg)
    fixed = " ".join(w["word"] for w in words)
    raw_en, fixed_en = TR.translate([msg, fixed])
    bubble = f"<div class='me'>{html.escape(msg)}</div>"
    left = (bubble + f"<div class='seen'>Bot reads: “{html.escape(raw_en)}”</div>"
            f"<div class='bot'>{html.escape(bot_reply(raw_en))}</div>")
    right = (bubble + f"<div class='seen ok'>Bot reads: “{html.escape(fixed_en)}”</div>"
             f"<div class='bot good'>{html.escape(bot_reply(fixed_en))}</div>")
    inside = (f"<div class='inside'><div class='k'>Inside the system, Qalaisyn turned the message into</div>"
              f"<div class='v'>{restored_html(words)}</div></div>")
    return left, right, inside


# ------------------------------------------------------------------ look-inside view
def look(msg):
    msg = clean(msg)
    if not msg:
        return "<div class='empty'>Type a message, or pick an example.</div>"
    if looks_english(msg):
        return NOT_KAZAKH
    words = QAL.restore_with_confidence(msg)
    fixed = " ".join(w["word"] for w in words)
    before, after = TR.translate([msg, fixed])
    return ("<div class='res'>"
            f"<div class='box before'><div class='k'>A translator reads the message as typed</div>"
            f"<div class='v'>{html.escape(before)}</div></div>"
            f"<div class='box fixed'><div class='k'>Qalaisyn restores the Kazakh letters (highlighted)</div>"
            f"<div class='v'>{restored_html(words)}</div>"
            f"<div class='lat'>Same text in the official Kazakh Latin alphabet (2021): <b>{html.escape(to_latin(fixed))}</b></div></div>"
            f"<div class='box after'><div class='k'>The translator reads it after Qalaisyn</div>"
            f"<div class='v'>{html.escape(after)}</div></div></div>")


# ------------------------------------------------------------------ page
CSS = """
body, gradio-app {background:#F4F6F8!important}
.gradio-container {background:#F4F6F8!important; max-width:1120px!important; margin:0 auto!important;
  font-family:'Golos Text','Segoe UI',sans-serif!important; color:#1B2433}
footer {display:none!important}
.brand {font-weight:700; font-size:17px; color:#1F6F78} .brand b {color:#E3A72F}
#hero h1 {font-size:40px; line-height:1.12; letter-spacing:-.02em; font-weight:700; margin:8px 0 10px; max-width:860px}
#hero p.sub {font-size:18px; line-height:1.55; color:#5F6B7A; max-width:740px; margin:0}
.sec {margin-top:28px} .sec h2 {font-size:23px; font-weight:700; margin:0 0 6px} .sec p.lead {font-size:16px; color:#5F6B7A;
  line-height:1.55; max-width:780px; margin:0 0 14px}
.why {display:grid; grid-template-columns:1.25fr 1fr; gap:14px}
.card {background:#fff; border:1px solid #DCE1E7; border-radius:16px; padding:18px 20px}
.words {display:flex; gap:14px; align-items:stretch; margin:6px 0 12px}
.w {flex:1; border-radius:12px; padding:12px 14px; border:1px solid #DCE1E7}
.w .kz {font-size:30px; font-weight:700} .w .en {font-size:15px; color:#5F6B7A}
.w.good {background:#E3F1F1; border-color:#C4E0E0} .w.bad {background:#F7E9E4; border-color:#EBCFC6}
.lt {background:#FBEFD2; box-shadow:inset 0 -3px 0 #E3A72F; border-radius:3px; padding:0 1px}
.card p {font-size:15.5px; line-height:1.55; margin:6px 0 0}
.analogy {font-size:15px; color:#5F6B7A}
.flow {display:flex; align-items:stretch; gap:0; margin:10px 0 4px; flex-wrap:wrap}
.node {background:#fff; border:1px solid #DCE1E7; border-radius:12px; padding:12px 14px; min-width:150px; flex:1}
.node .t {font-weight:700; font-size:15.5px} .node .d {font-size:13.5px; color:#5F6B7A; margin-top:3px; line-height:1.4}
.node.q {background:#1F6F78; border-color:#1F6F78; color:#fff} .node.q .d {color:#D6ECEC}
.arrow {display:flex; align-items:center; padding:0 8px; color:#9AA5B1; font-size:22px}
.server {border:2px dashed #B9C3CE; border-radius:16px; padding:10px; display:flex; align-items:stretch; flex:3; gap:0;
  position:relative; background:#FAFBFC}
.server .lab {position:absolute; top:-11px; left:14px; background:#F4F6F8; padding:0 6px; font-size:13px; color:#5F6B7A}
.cap {font-size:15px; color:#5F6B7A; margin-top:10px; line-height:1.5}
pre.code {background:#1B2433; color:#E6EDF3; border-radius:12px; padding:14px 16px; font-size:13.5px; line-height:1.55;
  overflow-x:auto; margin:10px 0 0}
pre.code .c {color:#8FA3B8}
.tabs {margin-top:6px}
.me {background:#E9F3F2; border:1px solid #CFE3E1; border-radius:16px 16px 16px 4px; padding:10px 14px; font-size:18px;
  display:inline-block; margin:4px 0 8px}
.seen {font-size:13.5px; color:#A8513B; margin:0 0 8px} .seen.ok {color:#1F6F78}
.bot {background:#F7E9E4; border:1px solid #EBCFC6; border-radius:16px 16px 4px 16px; padding:10px 14px; font-size:16.5px;
  line-height:1.45; margin-left:28px}
.bot.good {background:#E3F1F1; border-color:#C4E0E0}
.botcol h3 {font-size:16px; margin:0 0 8px} .botcol h3 span {font-weight:400; color:#5F6B7A}
.inside {background:#fff; border:1px dashed #B9C3CE; border-radius:14px; padding:12px 16px; margin-top:4px}
.inside .k, .box .k {font-size:14px; color:#5F6B7A; margin-bottom:6px} .inside .v {font-size:20px}
.res {display:grid; gap:12px}
.box {border-radius:14px; padding:14px 18px; border:1px solid #DCE1E7; background:white} .box .v {font-size:21px; line-height:1.45}
.box.before {background:#F7E9E4; border-color:#EBCFC6} .box.before .v {color:#A8513B}
.box.after {background:#E3F1F1; border-color:#C4E0E0} .box.after .v {color:#164E54; font-weight:500}
.unsure {text-decoration:underline dotted #B7791F 2px; text-underline-offset:6px}
.sugg {margin-top:10px; font-size:14.5px; color:#5F6B7A}
.chip {display:inline-block; margin:6px 6px 0 0; padding:3px 11px; border-radius:999px; background:#FFFBF1; border:1px solid #F0D9A6; color:#1B2433}
.lat {margin-top:10px; font-size:14px; color:#5F6B7A} .lat b {color:#1B2433; font-weight:500}
.empty {color:#5F6B7A; font-size:16px; padding:18px 4px}
#msg textarea, #msg2 textarea {font-size:19px!important; background:#E9F3F2!important; border:1px solid #CFE3E1!important;
  border-radius:16px 16px 16px 4px!important; padding:12px 14px!important}
button.go {background:#1F6F78!important; color:#fff!important; border:none!important; border-radius:12px!important; font-size:16px!important}
button.ex {background:#fff!important; border:1px solid #DCE1E7!important; border-radius:999px!important; color:#1B2433!important;
  font-weight:400!important; font-size:15px!important; box-shadow:none!important; justify-content:flex-start!important}
button.ex:hover {border-color:#1F6F78!important; color:#1F6F78!important}
.steps {display:grid; grid-template-columns:repeat(3,1fr); gap:14px}
.step {background:#fff; border:1px solid #DCE1E7; border-radius:14px; padding:16px 18px}
.step .n {display:inline-flex; width:28px; height:28px; border-radius:50%; background:#1F6F78; color:#fff; align-items:center;
  justify-content:center; font-weight:700; font-size:15px; margin-bottom:8px}
.step h3 {font-size:17px; margin:0 0 6px} .step p {font-size:15px; line-height:1.5; color:#5F6B7A; margin:0}
.facts {margin-top:18px; display:grid; grid-template-columns:repeat(3,1fr); gap:14px}
.fact {border-top:3px solid #1F6F78; padding-top:10px} .fact .big {font-size:28px; font-weight:700}
.fact p {font-size:14px; color:#5F6B7A; margin:2px 0 0; line-height:1.45}
.note {font-size:13px; color:#5F6B7A; margin:22px 0 8px}
@media (max-width:820px){ #hero h1{font-size:30px} .why,.steps,.facts{grid-template-columns:1fr} .flow{flex-direction:column}
  .arrow{justify-content:center; transform:rotate(90deg)} .server{flex-direction:column} }
"""

HERO = """
<div id="hero">
  <div class="brand">Qalaisyn<b>.</b></div>
  <h1>An engine inside chatbots and translators that understands Kazakh the way people really type it.</h1>
  <p class="sub">Most phones in Kazakhstan have a Russian keyboard, which has no letters for ә, ғ, қ, ң, ө, ұ, ү, і.
  People type the closest Russian letter, and AI systems misread them. Qalaisyn puts the letters back before the AI
  reads the message.</p>
</div>
"""

WHY = """
<div class="sec"><h2>Why one missing letter matters</h2>
<div class="why">
  <div class="card">
    <div class="words">
      <div class="w good"><div class="kz">өт</div><div class="en">go through, pass</div></div>
      <div class="w bad"><div class="kz">от</div><div class="en">fire</div></div>
    </div>
    <p>A Russian keyboard has no <span class="lt">ө</span>, so <i>“go through”</i> is typed as the word for
    <i>“fire”</i>. Real example: a passenger types <b>“ушак кешигип жатыр ма”</b>, meaning <i>“Is the plane late?”</i>.
    Without <span class="lt">ұ</span> and <span class="lt">қ</span> the word for <i>airplane</i> (ұшақ) is broken, and the
    airline's translator reads <i>“Is there a rumour going on?”</i></p>
    <p class="analogy">It is like writing Spanish without accents, where <i>papá</i> (dad) and <i>papa</i> (potato)
    become the same word, except that in Kazakh this happens in almost every second word.</p>
  </div>
  <div class="card">
    <p style="margin-top:0"><b>47%</b> of words typed on a Russian keyboard are misspelled in our tests.
    Over 13 million people speak Kazakh, and banks, airlines, clinics and e-government are moving their support to
    AI first. Every misread message is a wrong answer, a lost customer or a delayed emergency.</p>
    <p>The same problem exists wherever phones drop letters: Kyrgyz, Uzbek, Azerbaijani, Turkish, Vietnamese.
    The same code worked for Kyrgyz without changes.</p>
  </div>
</div></div>
"""

WHERE = """
<div class="sec"><h2>Where Qalaisyn lives</h2>
<p class="lead">Qalaisyn runs inside a company's system, between the incoming message and the AI that answers,
like a spell-checker inside a keyboard. Customers never see it and don't have to change anything.</p>
<div class="flow">
  <div class="node"><div class="t">Customer's phone</div><div class="d">types as usual:<br>“ушак кешигип жатыр ма”</div></div>
  <div class="arrow">→</div>
  <div class="server"><span class="lab">inside the company's system</span>
    <div class="node q"><div class="t">Qalaisyn</div><div class="d">puts the letters back:<br>“ұшақ кешігіп жатыр ма”<br>in milliseconds</div></div>
    <div class="arrow">→</div>
    <div class="node"><div class="t">Their AI</div><div class="d">chatbot, translator, search, spam filter</div></div>
  </div>
  <div class="arrow">→</div>
  <div class="node"><div class="t">Right answer</div><div class="d">“Flight KC 852 is delayed by 40 minutes.”</div></div>
</div>
<pre class="code"><span class="c"># how a company adds it: one call before its own AI</span>
from qalaisyn import restore
text = restore(message)          <span class="c"># "ушак кешигип жатыр ма" -> "ұшақ кешігіп жатыр ма"</span>
reply = support_bot.answer(text)</pre>
</div>
"""

HOW = """
<div class="sec"><h2>How the engine decides</h2>
<div class="steps">
  <div class="step"><div class="n">1</div><h3>List the possible words</h3>
    <p>Each typed word could be several Kazakh words: “от” → от (fire) or өт (go), “ушак” → ұшақ (airplane).
    Qalaisyn lists the real words it could be.</p></div>
  <div class="step"><div class="n">2</div><h3>Pick the most likely sentence</h3>
    <p>A language model trained on 1.5 million Kazakh sentences knows which words go together (“plane … late”),
    and the Viterbi algorithm picks the best whole sentence.</p></div>
  <div class="step"><div class="n">3</div><h3>Ask only when unsure</h3>
    <p>Every word gets a probability. Below 90% it becomes a suggestion instead of a silent change,
    about 1 word in 16. Russian words like “короче” are left alone.</p></div>
</div>
<div class="facts">
  <div class="fact"><div class="big">88% vs 80%</div><p>messages with every word right on a Russian keyboard: Qalaisyn vs a dictionary lookup; with typos 74% vs 49% (held-out test)</p></div>
  <div class="fact"><div class="big">47% → 3.5%</div><p>misspelled words on a Russian keyboard, before and after Qalaisyn</p></div>
  <div class="fact"><div class="big">62%</div><p>of Qalaisyn's mistakes are among the 6% of words it marks as unsure</p></div>
</div>
<p class="note">Prototype for the Veritas AI High School Hackathon 2026, Languages track. Translator: NLLB-200 (Meta).
The support bot on this page is a simple keyword bot for demonstration only, and the examples were chosen to show
the idea; overall results on held-out test data are in the project notebook. The engine runs in about 7 ms per
message on a laptop and needs about 1.3 GB of memory. Not for medical or emergency use.</p>
</div>
"""

theme = gr.themes.Base(font=[gr.themes.GoogleFont("Golos Text"), "Segoe UI", "sans-serif"])
with gr.Blocks(title="Qalaisyn", css=CSS, theme=theme) as demo:
    gr.HTML(HERO)
    gr.HTML(WHY)
    gr.HTML(WHERE)
    gr.HTML("<div class='sec'><h2>See it inside a support chatbot</h2><p class='lead'>The same simple support bot twice. "
            "On the left it reads the message as typed; on the right Qalaisyn runs inside it first. "
            "Pick a situation or type your own message.</p></div>")
    with gr.Row():
        sc_btns = [gr.Button(label, elem_classes="ex", size="sm") for label, _ in SCENARIOS]
    with gr.Row():
        cin = gr.Textbox(value=SCENARIOS[1][1], label="Customer's message (typed on a Russian keyboard)", elem_id="msg", scale=5)
        cgo = gr.Button("Send", elem_classes="go", scale=1)
    with gr.Row(equal_height=False):
        with gr.Column(elem_classes="botcol"):
            gr.HTML("<h3>Support bot today <span>(reads the message as typed)</span></h3>")
            left = gr.HTML()
        with gr.Column(elem_classes="botcol"):
            gr.HTML("<h3>Same bot with Qalaisyn inside</h3>")
            right = gr.HTML()
    inside = gr.HTML()

    gr.HTML("<div class='sec'><h2>Look inside the engine</h2><p class='lead'>Any message, word by word: what a "
            "translator understands before and after, which letters Qalaisyn put back, and where it is unsure.</p></div>")
    with gr.Row(equal_height=False):
        with gr.Column(scale=5):
            lin = gr.Textbox(value=EXAMPLES_RU[0], label="A message typed like in a chat", lines=2, elem_id="msg2")
            lgo = gr.Button("Restore and translate", elem_classes="go")
            ex_btns = [gr.Button(e, elem_classes="ex", size="sm") for e in EXAMPLES_RU + EXAMPLES_LAT]
        with gr.Column(scale=6):
            lout = gr.HTML()
    gr.HTML(HOW)

    cgo.click(chat, cin, [left, right, inside])
    cin.submit(chat, cin, [left, right, inside])
    for b, (_, text) in zip(sc_btns, SCENARIOS):
        b.click(lambda t=text: t, None, cin).then(chat, cin, [left, right, inside])
    lgo.click(look, lin, lout)
    lin.submit(look, lin, lout)
    for b, text in zip(ex_btns, EXAMPLES_RU + EXAMPLES_LAT):
        b.click(lambda t=text: t, None, lin).then(look, lin, lout)
    demo.load(chat, cin, [left, right, inside]).then(look, lin, lout)

if __name__ == "__main__":
    demo.launch(share="--share" in sys.argv)
