"""Generate Qalaisyn.ipynb (the submission notebook) from the source files and results."""
import json
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).parent
chrf = json.loads((ROOT / "results/translation_chrf.json").read_text())
t = chrf["test_tatoeba"]
f = chrf["test_flores"]


def rec(d, g="all", m="M2 Qalaisyn+typos"):
    return (d[f"{g}|{m}"] - d[f"{g}|B0 raw chat"]) / (d[f"{g}|gold"] - d[f"{g}|B0 raw chat"])


lost = 1 - t["all|B0 raw chat"] / t["all|gold"]
tc = chrf["test_tatoeba_cyr"]
fc = chrf["test_flores_cyr"]
lost_c = 1 - tc["all|B0 raw chat"] / tc["all|gold"]
conf = json.loads((ROOT / "results/confidence.json").read_text(encoding="utf-8"))
cc = conf["test_tatoeba_cyr"]["at_threshold"]
ky = json.loads((ROOT / "results/kyrgyz.json").read_text(encoding="utf-8"))

nb = nbf.v4.new_notebook()
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))  # noqa: E731
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))  # noqa: E731


SOURCES = []


def writefile(path):
    """Source files are collected into one collapsible section 0 so the story reads without code walls."""
    if path not in SOURCES:
        SOURCES.append(path)


md(f"""
# Qalaisyn — making AI understand Kazakh the way people actually text

**Track:** AI + Languages · **Veritas AI International High School Hackathon 2026**

> **AI understands Kazakh only when it is written "properly" — and almost nobody texts that way.**

Most phones in Kazakhstan have a **Russian keyboard**, so people drop the Kazakh-only letters
(ә ғ қ ң ө ұ ү һ і) and type *"калайсын"* instead of *"қалайсың"*; others text in Latin (*"qalaisyn"*).
Translation and chatbot models are trained on standard Kazakh, so they misread real messages.
**Qalaisyn** is a small, fast AI layer that sits in front of any translator or chatbot — like autocorrect inside a
keyboard — and turns chat-style Kazakh back into standard Kazakh. When it is unsure, it says so and offers suggestions.

| Headline result (held-out test data, translator: NLLB-200) | Russian keyboard | Latin chat |
|---|---|---|
| Meaning lost when a translator reads the message as typed | **{lost_c:.0%}** | **{lost:.0%}** |
| Meaning recovered by Qalaisyn — everyday sentences | **{rec(tc):.0%}** | **{rec(t):.0%}** |
| Meaning recovered by Qalaisyn — news sentences | **{rec(fc):.0%}** | **{rec(f):.0%}** |
| Messy messages (15% typos) — dictionary vs. Qalaisyn | **{rec(chrf['test_tatoeba_cyr-typos-15'], 'all', 'B2 dictionary'):.0%} vs. {rec(chrf['test_tatoeba_cyr-typos-15']):.0%}** | **{rec(chrf['test_tatoeba_typos-15'], 'all', 'B2 dictionary'):.0%} vs. {rec(chrf['test_tatoeba_typos-15']):.0%}** |
| Words shown as suggestions · share of its mistakes they contain | **{cc['flagged_share']:.0%} · {cc['errors_caught']:.0%}** | **{conf['test_tatoeba']['at_threshold']['flagged_share']:.0%} · {conf['test_tatoeba']['at_threshold']['errors_caught']:.0%}** |
| Same code on Kyrgyz (no changes, Latin) | | **{ky['recovered']:.0%}** recovered |

*This project is a prototype. It is not a product for medical, financial or emergency use.*

**Contents:** 1 · The problem → 2 · Data → 3 · Simulating chat writing → 4 · Models → 5 · Restoration results →
6 · Does the meaning survive? (translation) → 7 · Messy messages (stress tests) → 7b · Kyrgyz →
7c · Knowing when it is unsure (suggestions) → 8 · Where it fails → 9 · Native-speaker check → 10 · Try it →
11 · Limitations, next steps, sources.
All source code is in the collapsed *Setup · Source code* section.
""")

md("""
## 1 · The problem — and who it is for

**User:** Gulnar, 62, from a village in Turkistan region. Her phone has only a Russian keyboard. One night her
grandson has a fever and she texts the clinic's chatbot:

> *баламнын кызуы 39 котерилди не истеу керек* — "my child's temperature rose to 39, what should I do"
> (standard Kazakh: *баламның қызуы 39 көтерілді не істеу керек*)

Banks, clinics and e-government services in Kazakhstan increasingly put AI first in line. If the AI cannot read
how people really write, the people who write "the way they text" get worse help — or none.
The same pattern exists for Uzbek, Kyrgyz, Azerbaijani, Turkish, Vietnamese, Yoruba and many other languages whose
special letters get dropped on phones.

**What goes in:** a Kazakh message as people type it (Russian keyboard or Latin). **What comes out:** standard
Kazakh that any downstream AI (translator, chatbot, search) can understand, plus suggestions for words it is unsure about.

**Where it lives:** not an app people download, but a layer inside other services (a bank's support chatbot, a
clinic bot, e-government, translators, a phone keyboard), like autocorrect.
""")

code("""
# Setup. On Google Colab this downloads everything (≈200 MB); locally it reuses existing files.
import os, sys, json, subprocess
from pathlib import Path
IN_COLAB = "google.colab" in sys.modules
ROOT = Path(".").resolve()
(ROOT / "src").mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))
if IN_COLAB:
    subprocess.run("pip -q install sacrebleu pyarrow transformers==4.46.3 sentencepiece", shell=True)
print("Running on Colab:", IN_COLAB)
""")

md("""
## 2 · Data

All data is public. Nothing from a test set is used for training.

| Purpose | Dataset | Size |
|---|---|---|
| Training text (language model + vocabulary) | Kazakh Wikipedia (Nov 2023 dump) | 1.5 M sentences |
| Training text, conversational | Tatoeba Kazakh sentences (not in test) | ~4 k sentences |
| **Test 1 — everyday sentences** | Tatoeba Kazakh–English pairs | 623 sentences |
| **Test 2 — news sentences** | FLORES-200 `devtest` (Kazakh + professional English) | 1,012 sentences (300 for translation) |
| Tuning only | FLORES-200 `dev` | 997 sentences |
| Native-speaker test | messages written and corrected by our team member | see section 9 |
""")
writefile("src/chatify.py")
writefile("src/build_data.py")
code("""
# Build the corpus and test sets (downloads raw data on Colab).
RAW = ROOT / "data" / "raw"; RAW.mkdir(parents=True, exist_ok=True)
def get(url, name):
    if not (RAW / name).exists():
        subprocess.run(f'curl -sL -o "{RAW / name}" "{url}"', shell=True, check=True)
get("https://downloads.tatoeba.org/exports/per_language/kaz/kaz_sentences.tsv.bz2", "kaz_sentences.tsv.bz2")
get("https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences.tsv.bz2", "eng_sentences.tsv.bz2")
get("https://downloads.tatoeba.org/exports/per_language/kaz/kaz-eng_links.tsv.bz2", "kaz-eng_links.tsv.bz2")
get("https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz", "flores200.tar.gz")
get("https://huggingface.co/datasets/wikimedia/wikipedia/resolve/main/20231101.kk/train-00000-of-00001.parquet", "kkwiki.parquet")
if not (RAW / "kaz_sentences.tsv").exists():
    subprocess.run(f'cd "{RAW}" && bunzip2 -kf *.bz2 && tar -xzf flores200.tar.gz --wildcards "*kaz_Cyrl*" "*eng_Latn*" "*kir_Cyrl*"', shell=True)
P = ROOT / "data" / "processed"
if not (P / "test_tatoeba.jsonl").exists():
    import build_data; build_data.main()
for n in ["train_wiki.txt", "train_tatoeba.txt"]:
    print(n, sum(1 for _ in open(P / n, encoding="utf-8")), "sentences")
for n in ["test_tatoeba", "test_flores", "dev_flores"]:
    print(n, sum(1 for _ in open(P / f"{n}.jsonl", encoding="utf-8")), "messages (sentences x 4 writing styles)")
""")

md("""
## 3 · Simulating how people really type

We cannot use other people's private chats, so we **simulate writers**. Each simulated writer has a profile of
typing habits and keeps the same habit inside one message, like real people do.

**Cyrillic (the most common case):**
* **ru-keyboard** — a Russian keyboard: қ→к, ә→а, ө→о, ң→н, ұ/ү→у, ғ→г, һ→х, і→и (sometimes ы or Latin i)
* **partial** — has a Kazakh keyboard but types only some Kazakh letters

**Latin:**
* **careful** — close to the official Latin alphabet (q, ä, ö, ü)
* **typical** — q for қ, but drops the other special letters
* **minimal** — plain ASCII only, k for both к and қ
* **mixed** — switches habits inside a message

Real messages from a native speaker are tested separately in section 9.
""")
writefile("src/build_cyr.py")
code("""
import random
from chatify import chatify, chatify_cyr, PROFILE_NAMES, CYR_PROFILES
for s in ["Баламның қызуы 39 көтерілді, не істеу керек?", "Картадан ақша кетіп қалды, мен ештеңе сатып алған жоқпын."]:
    print(s)
    for p in CYR_PROFILES:
        print(f"   {p:12s} -> {chatify_cyr(s, p, random.Random(3))}")
    for p in PROFILE_NAMES:
        print(f"   {p:12s} -> {chatify(s, p, random.Random(3))}")
if not (P / "test_tatoeba_cyr.jsonl").exists():
    import build_cyr
""")

md("""
## 4 · Models

Restoring the letters is a guessing game that needs context: is `к`/`k` **к** or **қ**? is `а`/`a` **а** or **ә**?
is `и`/`i` **и** or **і**? is `н`/`n` **н** or **ң**? We compare five systems, from doing nothing to ours:

| Code | System | Idea |
|---|---|---|
| B0 | *raw chat* | give the chat text to the translator unchanged (size of the problem) |
| B1 | *letter rules* | every Latin letter → its most common Cyrillic letter (for Cyrillic input this changes almost nothing) |
| B2 | *dictionary* | every word → the most frequent Kazakh word that matches its letters (a strong simple baseline) |
| M1 | **Qalaisyn** | candidate words + typing-habit model + **word bigram language model** decoded with **Viterbi** over the whole sentence; unknown words are restored by a **character 5-gram model** |
| M2 | **Qalaisyn + typo search** | M1, plus: if a word is unknown or rare, also consider real words one edit away (symmetric-delete index) |

All settings of M1/M2 were tuned on FLORES `dev` only.
""")
writefile("src/restore.py")
writefile("src/eval_restore.py")
code("""
import time
from eval_restore import load_lexicon, load, evaluate
from restore import RuleRestorer, DictRestorer, QalaisynRestorer
t0 = time.time()
lex = load_lexicon()           # trains on 1.5 M sentences (cached after the first run)
lex.build_fuzzy()
print(f"vocabulary {len(lex.uni):,} words · {len(lex.bi):,} word pairs · {time.time()-t0:.0f}s")
RESTORERS = [RuleRestorer(), DictRestorer(lex), QalaisynRestorer(lex),
             QalaisynRestorer(lex, fuzzy=True, name="M2 Qalaisyn+typos")]
for msg in ["баламнын кызуы 39 котерилди не истеу керек", "balamnyn qyzuy 39 koterildi ne isteu kerek"]:
    print(msg)
    for r in RESTORERS:
        print(f"   {r.name:18s} {r.restore(msg)}")
""")

md("""
## 5 · Restoration results (held-out test sets)

**WER** = share of words restored wrongly, **CER** = share of letters restored wrongly (lower is better).
""")
code("""
import pandas as pd
tables = {}
for name in ["test_tatoeba_cyr", "test_flores_cyr", "test_tatoeba", "test_flores"]:
    tab, _ = evaluate(RESTORERS, load(name), name)
    tables[name] = tab
    df = pd.DataFrame({k: v for k, v in tab.items() if "|" not in k}).T.sort_index()
    print(f"\\n{name}"); display(df.style.format("{:.1%}"))
""")
code("""
# Results broken down by writing style (the brief asks for per-group results)
rows = []
for name, tab in tables.items():
    for k, v in tab.items():
        if "|" in k:
            m, prof = k.split("|"); rows.append({"test": name, "model": m, "style": prof, "WER": v["WER"]})
display(pd.DataFrame(rows).pivot_table(index=["test", "model"], columns="style", values="WER").style.format("{:.1%}"))
""")

md("""
## 6 · Does the meaning survive? Translation test

The real question is not letters but **meaning**. We translate every version into English with Meta's free
**NLLB-200** model (`facebook/nllb-200-distilled-600M`) and compare with the **professional English translation**
using **chrF** (higher is better). *Proper Kazakh text* is the ceiling.

`recovered = (system − raw chat) / (proper text − raw chat)`
""")
writefile("src/eval_translate.py")
code("""
# Translating ~20k sentences takes a while on a laptop GPU, so the notebook loads the saved scores
# produced by `python src/eval_translate.py ...` (run it to reproduce; translations are cached).
chrf = json.loads(Path("results/translation_chrf.json").read_text())
conds = ["gold", "B0 raw chat", "B1 rules", "B2 dictionary", "M1 Qalaisyn", "M2 Qalaisyn+typos"]
out = []
for name in ["test_tatoeba_cyr", "test_flores_cyr", "test_tatoeba", "test_flores"]:
    d = chrf[name]
    row = {c: d[f"all|{c}"] for c in conds}
    row["recovered (M2)"] = (row["M2 Qalaisyn+typos"] - row["B0 raw chat"]) / (row["gold"] - row["B0 raw chat"])
    out.append(pd.Series(row, name=name))
display(pd.DataFrame(out).style.format({c: "{:.1f}" for c in conds} | {"recovered (M2)": "{:.0%}"}))
""")
code("""
from IPython.display import Image, display
display(Image("figures/main_test_tatoeba_cyr.png", width=760))
display(Image("figures/main_test_tatoeba.png", width=760))
""")
code("""
# Side by side: what the translator produced before and after Qalaisyn (Russian-keyboard messages)
tr_rows = [json.loads(l) for l in open("data/processed/translated_test_tatoeba_cyr.jsonl", encoding="utf-8")]
ex = [r for r in tr_rows if r["profile"] == "ru-keyboard" and r["chat"] != r["gold"]][5:13]
display(pd.DataFrame([{"chat message": r["chat"], "translation as typed": r["en|B0 raw chat"],
                       "translation after Qalaisyn": r["en|M2 Qalaisyn+typos"], "professional": r["eng"]} for r in ex]))
""")

md("""
## 7 · Real messages are messy — stress tests

Our clean simulation could be *too easy*, because the test messages follow the same habits the model knows. So we
asked our own question: **when does Qalaisyn break?**

* **typos-5 / typos-15:** 5% / 15% of words get a thumb typo (dropped, doubled or swapped letter);
  tested on Latin and on Russian-keyboard messages (`cyr-typos-15`)
* **unseen spellings:** a writer with habits the model was never designed for: `ae` for ә, `oe` for ө, `kh` for х, `kk` for қ

This test exposed a weakness of M1, which led to M2 (typo search). The cost: M2 is slightly worse on perfectly
clean text, but much more robust on messy text. Since real messages are messy, **M2 is our final model.**
""")
writefile("src/stress.py")
code("""
from stress import build
stress_rows = []
for kind in ["cyr-typos-15", "typos-5", "typos-15", "unseen-habits"]:
    tab, outs = evaluate(RESTORERS, build(load("test_tatoeba"), kind), f"test_tatoeba_{kind}")
    for k, v in tab.items():
        if "|" not in k: stress_rows.append({"condition": kind, "model": k, "WER": v["WER"]})
    print(f"{kind:14s} e.g. {outs[7]['chat']}  ->  {outs[7]['M2 Qalaisyn+typos']}")
display(pd.DataFrame(stress_rows).pivot(index="model", columns="condition", values="WER").style.format("{:.1%}"))
display(Image("figures/messy_messages.png", width=760))
""")

md("""
### 7b · Does it transfer to another language? Kyrgyz

Kyrgyz shares the letters ң, ө, ү with Kazakh, and Kyrgyz speakers also text in Latin. We ran **exactly the same code**
with no changes, trained only on Kyrgyz Wikipedia, and tested on FLORES-200 Kyrgyz (300 sentences × 2 writing styles).
""")
writefile("src/kyrgyz.py")
code("""
ky = json.loads(Path("results/kyrgyz.json").read_text(encoding="utf-8"))   # produced by: python src/kyrgyz.py
print(f"Kyrgyz training sentences: {ky['train_sentences']:,}")
display(pd.DataFrame({"word error rate": ky["wer"]}).style.format("{:.1%}"))
display(pd.DataFrame({"chrF": ky["chrf"]}).style.format("{:.1f}"))
print(f"Meaning recovered for Kyrgyz: {ky['recovered']:.0%}")
display(pd.DataFrame(ky["examples"]))
""")

md("""
### 7c · Knowing when it is unsure — suggestions instead of silent mistakes

**Why.** Every model makes mistakes; the dangerous ones are *silent* mistakes. In a clinic or bank chat, a wrong
word should not be changed without anyone noticing. But asking the user about every word would be annoying.

**How.** For every word, Qalaisyn computes the probability that its choice is right, using the **forward-backward
algorithm** over the same candidate lattice and language model (it sums over *all* possible sentences, not just
the best one). If the probability is below a threshold, the word is shown as a **suggestion with 2–3 options**,
like autocorrect on a phone, instead of being changed silently. A chatbot can also skip asking and use both
options itself; asking the person makes sense only for important messages (money, health).

**Threshold.** Chosen on FLORES `dev` only: the threshold that catches the most mistakes while flagging at most
~6% of words.

**How we measure it (held-out test sets):** how many words get flagged (should be few), what share of all mistakes
fall among the flagged words (should be high), and whether the right word is among the suggestions.
""")
writefile("src/confidence.py")
code("""
conf = json.loads(Path("results/confidence.json").read_text(encoding="utf-8"))   # produced by: python src/confidence.py
print("threshold chosen on dev:", conf["threshold"])
rows = []
for name, label in [("test_tatoeba_cyr", "Russian keyboard, everyday"), ("test_flores_cyr", "Russian keyboard, news"),
                    ("test_tatoeba", "Latin chat, everyday")]:
    a = conf[name]["at_threshold"]
    rows.append({"test": label, "words": a["words"], "word error rate": a["error_rate"],
                 "words shown as suggestions": a["flagged_share"], "mistakes among them": a["errors_caught"],
                 "right word among the suggestions": a["fixed_by_top3_among_flagged_errors"],
                 "error rate of the words it is sure about": a["error_rate_unflagged"]})
display(pd.DataFrame(rows).set_index("test").style.format({c: "{:.1%}" for c in rows[0] if c not in ("test", "words")}))
print("Is the confidence honest? (Russian keyboard, everyday)")
display(pd.DataFrame(conf["test_tatoeba_cyr"]["calibration"]).style.format({"actually_correct": "{:.1%}"}))
display(Image("figures/confidence.png", width=640))
q = RESTORERS[-1]
for m in ["erekshe atap ot", "салем калайсын ертен мектепке барасын ба"]:
    print(m)
    for w in q.restore_with_confidence(m):
        flag = "  <- suggestion: " + " / ".join(f"{a} {p:.0%}" for a, p in w["alternatives"] if p > 0.03) if w["confidence"] < conf["threshold"] else ""
        print(f"   {w['typed']:12s} -> {w['word']:12s} {w['confidence']:.0%}{flag}")
""")
md(f"""
**Result.** On Russian-keyboard messages Qalaisyn shows only **{cc['flagged_share']:.0%} of words** as suggestions,
and those words contain **{cc['errors_caught']:.0%} of all its mistakes**; for
**{cc['fixed_by_top3_among_flagged_errors']:.0%}** of them the right word is among the suggestions. Words it is sure
about are wrong only **{cc['error_rate_unflagged']:.1%}** of the time. The confidence is also honest: words rated
above 99% are right about 99% of the time. Honest limit: about 4 in 10 mistakes are still made with high confidence
(mostly н/ң and і/и pairs where both words exist).
""")

md("""
## 8 · Where it fails, and why
""")
writefile("src/analysis.py")
code("""
import analysis
data = sum((analysis.rows(n) for n in ["test_tatoeba", "test_flores", "test_tatoeba_cyr", "test_flores_cyr"]), [])
rates, conf = analysis.letter_errors(data)
display(pd.DataFrame([{"correct letter": a, "Qalaisyn wrote": b, "times": n} for (a, b), n in conf.most_common(8)]))
order = ["1-4 words", "5-8 words", "9-15 words", "16+ words"]
bl = analysis.by_length(data)
display(pd.DataFrame({"word error rate": {k: bl[k] for k in order}}).style.format("{:.1%}"))
display(Image("figures/letters.png", width=640))
fails = analysis.failures(analysis.rows("test_tatoeba_cyr"), n=40)
display(pd.DataFrame([{"chat": x["chat"], "ours": x["ours"], "reference": x["gold"],
                       "wrong words (reference, ours)": x["wrong"]} for x in fails[::4]]))
""")
md("""
**What we learned from the failures**

1. **н vs ң and і vs ы vs и** are the hardest letters: these pairs often produce two real words (e.g. *-ның* vs
   *-нің* endings after an ambiguous vowel), so only context can decide, and our bigram context is short.
2. **True ambiguity:** *ot* can be **от** (fire) or **өт** (pass/go) — "Erekshe atap ot!" is a one-word-context case.
3. **Some "errors" are mistakes in the reference.** Tatoeba writes *қагаз* and *сатыл ал*; the correct spellings are
   **қағаз** (paper) and **сатып ал** (buy) — exactly what Qalaisyn produced. Our scores are therefore slightly
   pessimistic.
4. **Unseen spellings** (`kk`, `ae`) are still the weakest condition (≈13–15% word errors), see section 7.
""")

md("""
## 9 · Native-speaker check

A native Kazakh speaker on our team writes real messages exactly the way they text friends, plus the correct
Cyrillic version (`data/real/real_messages.csv`). These messages are never used during development; the cell below
scores whatever is in the file.
""")
code("""
real = Path("data/real/real_messages.csv")
if real.exists():
    import csv
    rr = [r for r in csv.DictReader(open(real, encoding="utf-8")) if r["how_i_would_text"].strip()]
    rows = [{"id": r["id"], "kaz": r["correct_kazakh_cyrillic"], "chat": r["how_i_would_text"],
             "gold": __import__("chatify").normalize_cyr(r["correct_kazakh_cyrillic"]), "profile": "real",
             "eng": r.get("english", "")} for r in rr]
    tab, outs = evaluate(RESTORERS, rows, "real")
    display(pd.DataFrame({k: v for k, v in tab.items() if "|" not in k}).T.style.format("{:.1%}"))
    display(pd.DataFrame([{"as typed": o["chat"], "Qalaisyn": o["M2 Qalaisyn+typos"], "correct": o["gold"]} for o in outs]))
else:
    print("Native-speaker messages not added yet (data/real/real_messages.csv).")
""")

md("""
## 10 · Try it

Restore and translate any message. Run `python src/app.py --share` for the interactive Gradio demo (screenshot below).
""")
code("""
from IPython.display import Image, display
display(Image("figures/demo.jpg", width=620))
display(Image("figures/demo_suggestions.jpg", width=620))   # dotted words = not sure, with suggestions
""")
code("""
import warnings; warnings.filterwarnings("ignore")
from eval_translate import Translator
TR = Translator()
qal = RESTORERS[-1]
for m in ["баламнын кызуы 39 котерилди не истеу керек",
          "ажеме жедел жардем керек уйге келиниз",
          "kartadan aqsha ketip qaldy men eshtene satyp algan joqpyn"]:
    fixed = qal.restore(m)
    before, after = TR.translate([m, fixed])
    print(f"chat:   {m}\\n  AI as typed:  {before}\\n  Qalaisyn:     {fixed}\\n  AI after:     {after}\\n")
""")

md("""
*Note on the last example:* Qalaisyn restored every word correctly, but the translator dropped the first half of the sentence
("money disappeared from my card"). That is a limit of the translation model, not of the restoration — and a reminder
that chrF also measures the translator's own mistakes, which are the same for every system we compare.
""")

md("""
## 11 · Limitations, next steps and sources

**Limitations**
* Chat-style test messages are simulated from typing-habit profiles; the native-speaker set is small.
* The language model is trained mostly on Wikipedia, which is more formal than chats.
* Translation quality is measured automatically with chrF on 623 + 300 sentences.
* Russian words written in Latin inside Kazakh messages are not handled yet.

**Next steps**
1. A longer context model (word trigrams or a small neural model) for the н/ң and і/ы/и cases.
2. More languages (Kyrgyz already works with zero code changes, section 7b; Uzbek, Azerbaijani next) and a plug-in
   for chatbots of public services.

**Sources and tools**
* Data: [Tatoeba](https://tatoeba.org) (CC BY 2.0 FR) · [FLORES-200](https://github.com/facebookresearch/flores) (CC BY-SA 4.0) ·
  [Kazakh Wikipedia via Hugging Face `wikimedia/wikipedia`](https://huggingface.co/datasets/wikimedia/wikipedia) (CC BY-SA)
* Model: [NLLB-200 distilled 600M](https://huggingface.co/facebook/nllb-200-distilled-600M) (Meta, CC BY-NC 4.0) — used only for evaluation
* Libraries: PyTorch, Hugging Face Transformers, sacrebleu (chrF), pandas, matplotlib, Gradio
* AI tools: Claude (Anthropic) helped write code and text; every part was reviewed and explained to the team.

*This project is a prototype and is not medical or financial advice.*
""")

# ---- insert the collapsible source-code section right after the setup cell
setup_idx = next(i for i, c in enumerate(cells) if "IN_COLAB = " in c.source)
head = nbf.v4.new_markdown_cell(
    "## Setup · Source code (collapsed — click to expand)\n\n"
    "All code of the project. Each cell writes one file into `src/`; the sections below import it. "
    "Files: " + ", ".join(f"`{p}`" for p in SOURCES) + ".")
head["id"] = "source-code"
src_cells = [head] + [nbf.v4.new_code_cell(f"%%writefile {p}\n{(ROOT / p).read_text(encoding='utf-8').strip()}")
                      for p in SOURCES]
cells[setup_idx + 1:setup_idx + 1] = src_cells

nb["cells"] = cells
nb["metadata"]["colab"] = {"collapsed_sections": ["source-code"], "provenance": []}
nb["metadata"]["kernelspec"] = {"name": "qalaisyn", "display_name": "Python (Qalaisyn)", "language": "python"}
nbf.write(nb, ROOT / "Qalaisyn.ipynb")
print("written Qalaisyn.ipynb with", len(cells), "cells")
