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


REPO_URL = "https://github.com/ZemBono/qalaisyn"
DEMO_URL = "https://zembono.github.io/qalaisyn/web/"
val = json.loads((ROOT / "results/value.json").read_text(encoding="utf-8"))
vr, vt, vl = val["Russian keyboard, everyday"], val["Russian keyboard + 15% typos"], val["Latin, unseen spellings"]
real = json.loads((ROOT / "results/real.json").read_text(encoding="utf-8"))
rw = real["wer"]
kyr = ky.get("recovered_by_style", {"ru-keyboard": ky["recovered"]})["ru-keyboard"]

md(f"""
# Qalaisyn — an engine that lets AI understand Kazakh the way people really type it

**Track:** AI + Languages · **Veritas AI International High School Hackathon 2026**

Most phones in Kazakhstan have a **Russian keyboard**, which has no keys for the Kazakh letters
ә ғ қ ң ө ұ ү һ і. People type the closest Russian letter — *калайсын* instead of *қалайсың* — and the AI systems
that now answer bank, airline, clinic and government chats misread them. **Qalaisyn** is a small engine that runs
*inside* those systems and puts the letters back before the AI reads the message.

## Start here — the project in two minutes

**1 · Why one missing letter matters.** On a Russian keyboard *өт* ("go through") is typed as *от* ("fire").
A passenger asks an airline bot *ушак кешигип жатыр ма* — "is the plane late?" — and the translator reads
"is there a rumour going on?". It is like Spanish without accents, where *papá* (dad) and *papa* (potato) merge,
except that it happens in almost every second Kazakh word.

**2 · What Qalaisyn is.** An engine that works inside other systems: a layer in a company's system, between the
incoming message and the AI that answers — like a spell-checker inside a keyboard. Customers never see it.

1. The customer types on a phone as usual: *ушак кешигип жатыр ма*
2. Inside the company's system, **Qalaisyn** puts the letters back in a few milliseconds: *ұшақ кешігіп жатыр ма*
3. The company's own AI (chatbot, translator, search) now understands and answers: "Flight KC 852 is delayed by 40 minutes."

(The diagram and a live support-bot comparison are shown right below the setup cell and in section 10.)

**3 · Results at a glance** (held-out test data; full details below):

| | Message as typed | Dictionary lookup | **Qalaisyn** |
|---|---|---|---|
| Russian keyboard: words wrong | {vr["word_error_rate"]["as_typed"]:.0%} | {vr["word_error_rate"]["dictionary"]:.1%} | **{vr["word_error_rate"]["qalaisyn"]:.1%}** |
| Russian keyboard: messages with **every** word right | — | {vr["messages_fully_right"]["dictionary"]:.0%} | **{vr["messages_fully_right"]["qalaisyn"]:.0%}** |
| Russian keyboard + typos: messages fully right | — | {vt["messages_fully_right"]["dictionary"]:.0%} | **{vt["messages_fully_right"]["qalaisyn"]:.0%}** |
| Meaning recovered for a translator, Russian keyboard + typos | 0% | {rec(chrf['test_tatoeba_cyr-typos-15'], 'cyr-typos-15', 'B2 dictionary'):.0%} | **{rec(chrf['test_tatoeba_cyr-typos-15'], 'cyr-typos-15'):.0%}** |
| Meaning recovered, Latin with unseen spellings | 0% | {rec(chrf['test_tatoeba_unseen-habits'], 'unseen-habits', 'B2 dictionary'):.0%} | **{rec(chrf['test_tatoeba_unseen-habits'], 'unseen-habits'):.0%}** |
| Words shown as suggestions · share of its mistakes among them | — | cannot tell | **{cc['flagged_share']:.0%} · {cc['errors_caught']:.0%}** |
| Same code on Kyrgyz (Russian keyboard), meaning recovered | — | — | **{kyr:.0%}** |
| **{real["n"]} real messages written by a native speaker**: words wrong | {rw["B0 raw chat"]:.0%} | {rw["B2 dictionary"]:.1%} | **{rw["M2 Qalaisyn+typos"]:.1%}** (free ChatGPT 12.9%; {rw["M2 before native check"]:.1%} before two late rules) |

**Checked by a native speaker.** Beyond the simulated test sets, a native Kazakh speaker wrote {real["n"]} real
messages exactly as they text (slang, Russian words, shortened forms) together with the correct spelling. On these
messages {rw["B0 raw chat"]:.0%} of words are wrong as typed, {rw["B2 dictionary"]:.0%} after a dictionary
lookup, 12.9% after free ChatGPT and **{rw["M2 Qalaisyn+typos"]:.1%} after Qalaisyn**: a free offline engine makes
fewer mistakes than a giant online model (section 9).

**4 · Why a model and not just a dictionary?** On clean, carefully typed text a dictionary of the most common
spelling is already good, so we tested where it matters:
(a) **whole messages** — a chatbot needs every word right: Qalaisyn gets
{vr["messages_fully_right"]["qalaisyn"]:.0%} of messages fully right vs {vr["messages_fully_right"]["dictionary"]:.0%}
(+{(vr["messages_fully_right"]["qalaisyn"] - vr["messages_fully_right"]["dictionary"]) * 100:.0f} percentage points, 95% confidence interval
+{vr["messages_fully_right"]["diff_ci"][0] * 100:.0f} to +{vr["messages_fully_right"]["diff_ci"][1] * 100:.0f});
(b) **context** — it fixes {vr["dictionary_mistakes_fixed"]} of the dictionary's word mistakes while making
{vr["new_mistakes"]} new ones;
(c) **messy messages** — with typos the gap grows (table above);
(d) **knowing when it is unsure** — a dictionary always guesses silently; Qalaisyn flags its doubtful words.

**5 · Try it.** **Live demo, running in your browser: {DEMO_URL}** (type any message). Code: {REPO_URL}.
This notebook can also be run in Colab; all results are already saved below.

*Prototype — not for medical, financial or emergency use.*

**The details:** 1 · Problem and user → 2 · Data → 3 · Simulating how people type → 4 · Models → 5 · Restoration
results → 6 · Does the meaning survive? → 7 · Messy messages → 7b · Kyrgyz → 7c · Suggestions → 7d · Why not a
dictionary? → 8 · Where it fails → 9 · Native-speaker check → 10 · Try it yourself → 11 · Limitations and sources.
Code cells are folded ("Show code"); all source code is in the folded *Setup · Source code* section.
""")

code(f"""
#@title Setup (run first in Colab: downloads the project code and the trained model)
import os, sys, json, subprocess
from pathlib import Path
IN_COLAB = "google.colab" in sys.modules
REPO_URL = "{REPO_URL}"
if IN_COLAB and not Path("qalaisyn").exists():
    subprocess.run(f"git clone --depth 1 {{REPO_URL}} qalaisyn", shell=True, check=True)
    subprocess.run("pip -q install sacrebleu transformers==4.46.3 sentencepiece", shell=True)
if IN_COLAB:
    os.chdir("qalaisyn")
ROOT = Path(".").resolve()
(ROOT / "src").mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))
print("Running on Colab:", IN_COLAB)
""")

code("""
#@title Where Qalaisyn lives, and the same support bot with and without it (screenshots of the demo)
from IPython.display import Image, display
display(Image("figures/demo_where.jpg", width=760))
display(Image("figures/demo_chatbot.jpg", width=760))
""")

md("""
## 1 · The problem — and who it is for

**User:** Gulnar, 62, from a village in Turkistan region. Her phone has only a Russian keyboard. One night her
grandson has a fever and she texts the clinic's chatbot:

> *баламнын кызуы 39 котерилди не истеу керек* — "my child's temperature rose to 39, what should I do"
> (standard Kazakh: *баламның қызуы 39 көтерілді не істеу керек*)

**What goes in:** a Kazakh message as people type it (Russian keyboard or Latin). **What comes out:** standard
Kazakh (Cyrillic, or the new official Latin alphabet) that any downstream AI can understand, plus suggestions for
words it is unsure about.

**Why it matters every day.** Over 13 million people speak Kazakh, and support chats, clinics and government
services are moving to AI first. A misread message means a wrong answer, a lost customer or a delayed emergency.
The same pattern exists wherever phones drop letters (Kyrgyz, Uzbek, Azerbaijani, Turkish, Vietnamese).
Live examples from our model (translator: NLLB-200; examples chosen to illustrate, overall results below):

| Service | Message as typed | AI without Qalaisyn | AI with Qalaisyn |
|---|---|---|---|
| Bank support | *несие бойынша толемди кешиктирсем бола ма* | "Can I cash out the loan amount" | "can I delay payment on loan" |
| Airline support | *ушак кешигип жатыр ма* | "is there a rumor going on?" | "is the plane running late?" |
| E-government | *жеке куалигимди жогалтып алдым не истеу керек* | "I canceled my personal credentials or need to delete them" | "I lost my ID what to do" |
| Clinic chatbot | *баламнын кызуы 39 котерилди не истеу керек* | "fever of the child 39 caterilldi or eat" | "my baby has a fever of 39 what to do" |
""")

md("""
## 2 · Data

All data is public. Nothing from a test set is used for training.

| Purpose | Dataset | Size |
|---|---|---|
| Training text (language model + vocabulary) | Kazakh Wikipedia (Nov 2023 dump) | 1.5 M sentences |
| Training text, conversational (weighted ×20) | Tatoeba Kazakh sentences (not in test) + Kazakh film subtitles (OPUS OpenSubtitles) | ~8 k sentences |
| Russian words to leave alone | Russian word-frequency list (FrequencyWords, top 30k) | 30 k words |
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
| M2 | **Qalaisyn + typo search** (final) | M1, plus: real words one edit away for unknown/rare words (symmetric-delete index); Russian words inside the message are left alone; question particles typed together are split (*болама* → *бола ма*) |

All settings of M1/M2 were tuned on FLORES `dev` only. The Russian-word and particle rules were developed on a
separate set of draft chat messages, never on the test sets. To save memory, word pairs and words seen only once
are dropped: 7.1 M → 1.4 M pairs, memory 2.8 GB → 1.3 GB, with almost the same accuracy (word errors on dev
3.06% → 3.17% Latin, 2.68% → 2.63% Russian keyboard). The engine restores a message in about 7 ms on a laptop.
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
display(Image("figures/system_test_tatoeba_cyr.png", width=760))
display(Image("figures/system_test_tatoeba.png", width=760))
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
display(Image("figures/meaning.png", width=780))
""")

md("""
### 7b · Does it transfer to another language? Kyrgyz

Kyrgyz shares the letters ң, ө, ү with Kazakh, and Kyrgyz speakers also type on Russian keyboards or in Latin. We ran
**exactly the same code** with no changes, trained only on Kyrgyz Wikipedia, and tested on FLORES-200 Kyrgyz
(300 sentences × 3 writing styles: Russian keyboard, typical Latin, minimal Latin).
""")
writefile("src/kyrgyz.py")
code("""
ky = json.loads(Path("results/kyrgyz.json").read_text(encoding="utf-8"))   # produced by: python src/kyrgyz.py
print(f"Kyrgyz training sentences: {ky['train_sentences']:,}")
display(pd.DataFrame({"word error rate": ky["wer"]}).style.format("{:.1%}"))
display(pd.DataFrame(ky["chrf"]).style.format("{:.1f}"))
for st, r in ky.get("recovered_by_style", {}).items():
    print(f"Meaning recovered for Kyrgyz, {st}: {r:.0%}")
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
### 7d · Why a model and not just a dictionary?

A fair question: a dictionary that picks the most common spelling of each word is already good on clean text
(compare B2 and M2 in section 5). So we measured what a real system needs, with **95% bootstrap confidence
intervals** (1,000 resamples of the test messages) so that differences are not noise:

1. **Whole messages.** A chatbot needs *every* word right. We count messages restored with no mistake at all.
2. **Context.** How many of the dictionary's word mistakes Qalaisyn fixes, and how many new mistakes it makes.
3. **Messy messages.** Typos and unseen spellings, where the dictionary breaks down.
4. **Knowing when it is unsure** (section 7c): a dictionary always guesses silently.
""")
writefile("src/value.py")
code("""
val = json.loads(Path("results/value.json").read_text(encoding="utf-8"))   # produced by: python src/value.py
rows = []
for k, v in val.items():
    m, w = v["messages_fully_right"], v["word_error_rate"]
    row = {"test": k, "messages fully right: dictionary": m["dictionary"], "Qalaisyn": m["qalaisyn"],
           "difference (95% CI)": f"{m['qalaisyn'] - m['dictionary']:+.1%} [{m['diff_ci'][0]:+.1%}, {m['diff_ci'][1]:+.1%}]",
           "word errors: dictionary": w["dictionary"], "Qalaisyn ": w["qalaisyn"],
           "dictionary mistakes fixed / new mistakes": f"{v['dictionary_mistakes_fixed']} / {v['new_mistakes']}"}
    if "chrf" in v:
        c = v["chrf"]; row["chrF difference (95% CI)"] = f"{c['qalaisyn'] - c['dictionary']:+.1f} [{c['diff_ci'][0]:+.1f}, {c['diff_ci'][1]:+.1f}]"
    rows.append(row)
pct = {c: "{:.1%}" for c in ["messages fully right: dictionary", "Qalaisyn", "word errors: dictionary", "Qalaisyn "]}
display(pd.DataFrame(rows).set_index("test").style.format(pct))
display(Image("figures/messages.png", width=780))
""")
md("""
**Reading the table.** On every test the confidence interval for "messages fully right" lies above zero, so the
advantage is not noise; it is largest on messy messages. On clean news text the translation scores (chrF) of the
dictionary and Qalaisyn are close, which we report honestly: the value of the model is in getting whole real
messages right, in surviving typos, and in knowing when to ask.
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
## 9 · Native-speaker check: real messages

Simulated messages follow rules we wrote, so the real test is messages written by a person. A native Kazakh speaker
(a friend of the team, with permission) went through everyday situations and, for each one, typed the message
exactly as they would in a chat, then wrote its correct spelling (`data/real/ДЛЯ_ДРУГА.csv`). These messages were
never used for development or tuning. No English references exist for them, so meaning is measured against the
translation of the *correct* spelling.

Two numbers are reported. **"M2 before native check"** is the model exactly as it was when these messages first
arrived: the truly unseen result. After reading the errors we added two general rules, so the final M2 number on this
set is optimistic: (1) vowel harmony of the question particle (*керек па* → *керек пе*); (2) chat short forms, where a
final vowel is dropped after ш/д (*жберш* → *жіберші*, *болад* → *болады*), plus keeping everyday service names
(*каспи*, *егов*) and Russian *-ый* words as typed. On the held-out test sets (sections 5–6) these rules change
nothing (e.g. Russian keyboard, Tatoeba: 3.51% → 3.51% words wrong), so they do not hurt clean text.

**Comparison with ChatGPT.** We sent the same messages to the free ChatGPT web version (15 Nov 2026, one prompt,
instruction to restore the letters only; prompt and answers in `data/llm/`). Words wrong: ChatGPT **12.9%**,
Qalaisyn **11.9%** (ChatGPT still gets more whole messages exactly right: 59% vs 50%). Qalaisyn does this offline,
for free, in milliseconds, with a 21 MB model in the browser.
""")
writefile("src/real_eval.py")
code("""
import real_eval
real_rows = real_eval.load_rows()
if real_rows:
    tab, outs = evaluate(RESTORERS, real_rows, "real")
    print(f"{len(real_rows)} native-speaker messages")
    display(pd.DataFrame({k: v for k, v in tab.items() if "|" not in k}).T.style.format("{:.1%}"))
    rows = []
    for k, v in tab.items():
        if "|" in k:
            m, s = k.split("|"); rows.append({"model": m, "style": s, "WER": v["WER"]})
    display(pd.DataFrame(rows).pivot(index="model", columns="style", values="WER").style.format("{:.1%}"))
    display(pd.DataFrame([{"as typed": o["chat"], "Qalaisyn": o["M2 Qalaisyn+typos"], "correct": o["gold"],
                           "right?": "yes" if o["M2 Qalaisyn+typos"] == o["gold"] else "no"} for o in outs]))
else:
    print("Native-speaker messages are being collected (data/real/ДЛЯ_ДРУГА.csv).")
""")

md("""
## 10 · Try it yourself

Qalaisyn is an engine that runs **inside** other systems, between an incoming
message and the AI that answers it. The demo page is only a window into it:

1. *Why one missing letter matters* — explained for people who do not speak Kazakh;
2. *Where Qalaisyn lives* — the customer's phone → **Qalaisyn inside the company's system** → their AI → the answer;
3. *See it inside a support chatbot* — the same simple support bot twice: reading the message as typed, and with
   Qalaisyn inside. Without it the bot answers the wrong question (e.g. "how to withdraw cash" instead of
   "delay a loan payment"); with it, the bot answers correctly. (The bot is a simple keyword bot for demonstration;
   the replies come from the live model's translation.)
4. *Look inside the engine* — any message, word by word, with suggestions for unsure words.
""")
code("""
from IPython.display import Image, display
display(Image("figures/demo.jpg", width=760))
display(Image("figures/demo_where.jpg", width=760))
display(Image("figures/demo_chatbot.jpg", width=760))
""")
writefile("src/latin.py")
writefile("src/app.py")
md("""
**Run the demo yourself (Google Colab):** run all cells above (≈10 min the first time: it downloads the data and
the translation model), then run the next cell. It prints a public link to the demo page, valid for 72 hours.
""")
code("""
if IN_COLAB:
    subprocess.run("pip -q install gradio==5.9.1", shell=True)
    import app
    app.demo.launch(share=True, debug=False)
else:
    print("On a local machine run:  python src/app.py   (then open http://localhost:7860)")
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
* Most test messages are simulated from typing-habit profiles; the native-speaker set is small.
* The language model is trained mostly on Wikipedia (plus Tatoeba and film subtitles), which is more formal than
  chats. Merged question particles (*болама* → *бола ма*) and common Russian words (*доставка*, *короче*, *щас*) are
  now handled, but rarer colloquial forms and slang can still be "corrected" into the wrong Kazakh word.
* Rare word forms (seen fewer than twice in training) were dropped to save memory; typo search can then replace a
  rare but correct form with a more common neighbour (*телефоным* → *телефоны*).
* Translation quality is measured automatically with chrF.

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

for c in cells:
    if c.cell_type == "code" and not c.source.startswith("%%writefile"):
        if not c.source.startswith("#@title"):
            c.source = "#@title Show code\n" + c.source
        c.metadata["cellView"] = "form"
        c.metadata["tags"] = ["hide-input"]
nb["cells"] = cells
nb["metadata"]["colab"] = {"collapsed_sections": ["source-code"], "provenance": []}
nb["metadata"]["kernelspec"] = {"name": "qalaisyn", "display_name": "Python (Qalaisyn)", "language": "python"}
nbf.write(nb, ROOT / "Qalaisyn.ipynb")
print("written Qalaisyn.ipynb with", len(cells), "cells")
