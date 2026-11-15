# Qalaisyn — making AI understand Kazakh the way people actually text

**Veritas AI International High School Hackathon 2026 · Track: Languages**

> AI understands Kazakh only when it is written "properly" — and almost nobody texts that way.

Most phones in Kazakhstan have a Russian keyboard, so people type *калайсын* instead of *қалайсың* (others type
*qalaisyn* in Latin), and the AI behind bank, airline, clinic and government chats misreads them.
**Qalaisyn** is an engine that sits inside those systems, like a spell-checker inside a keyboard, and restores
standard Kazakh (Cyrillic or the new Latin alphabet) before the AI reads the message. When unsure, it shows
suggestions instead of guessing silently. About 7 ms per message, 1.3 GB of memory.

On held-out data (Russian keyboard): words misspelled 47% → 3.5% (dictionary baseline 5.8%); messages with every word
right 88% vs 80% (+9 pts, 95% CI +7…+11), with typos 74% vs 49%. 6% of words become suggestions and they contain 63%
of its mistakes. The same code works for Kyrgyz.

![messages](figures/messages.png)

* **Live demo:** Hugging Face Space (link added after publishing)

* **Notebook with all results:** [`Qalaisyn.ipynb`](Qalaisyn.ipynb)
* **One-page write-up:** [`WRITEUP.md`](WRITEUP.md) / `WRITEUP.pdf`

## Repository
| Path | What it is |
|---|---|
| `src/chatify.py` | simulates four chat typing styles, typos and unseen spellings |
| `src/build_data.py` | builds training text and held-out test sets |
| `src/restore.py` | B1 rules, B2 dictionary, M1/M2 Qalaisyn (candidates + habit model + bigram LM + Viterbi + char 5-gram + typo search) |
| `src/build_cyr.py` | Russian-keyboard / partial-keyboard Cyrillic test sets |
| `src/eval_restore.py`, `src/stress.py` | word/char error rates, stress tests |
| `src/confidence.py` | per-word confidence (forward-backward), suggestions, calibration |
| `src/value.py` | "why not a dictionary?" — whole-message accuracy, fixes vs breaks, bootstrap CIs |
| `src/latin.py` | output in the official Kazakh Latin alphabet (2021) |
| `data/lexicon.pkl` | the trained model (pruned language model, 95 MB) |
| `src/kyrgyz.py` | transfer test on Kyrgyz |
| `src/eval_translate.py` | NLLB-200 translation + chrF |
| `src/analysis.py`, `src/charts.py` | failure analysis and figures |
| `src/app.py` | Gradio demo |

## Reproduce
```bash
pip install numpy pandas scikit-learn sacrebleu matplotlib pyarrow torch transformers==4.46.3 sentencepiece gradio==5.9.1
# download raw data: see the setup cell in Qalaisyn.ipynb
python src/build_data.py && python src/build_cyr.py
for s in test_tatoeba test_flores test_tatoeba_cyr test_flores_cyr; do python src/eval_restore.py $s; done
python src/stress.py test_tatoeba && python src/stress.py test_flores
python src/eval_translate.py test_tatoeba test_flores test_tatoeba_cyr test_flores_cyr test_tatoeba_typos-5 test_tatoeba_typos-15 test_tatoeba_unseen-habits test_tatoeba_cyr-typos-15 test_flores_typos-15 test_flores_unseen-habits
python src/confidence.py && python src/kyrgyz.py && python src/value.py
python src/analysis.py && python src/charts.py
python src/app.py --share
```

*Prototype. Not for medical, financial or emergency use.* Sources and licences: see `WRITEUP.md`.
