# Qalaisyn — making AI understand Kazakh the way people actually text

**Veritas AI International High School Hackathon 2026 · Track: Languages**

> AI understands Kazakh only when it is written "properly" — and almost nobody texts that way.

Most Kazakhs text in Latin letters without the special Kazakh letters (*qalaisyn* instead of *қалайсың*).
A translator loses **75%** of the meaning of such messages. **Qalaisyn** restores standard Kazakh in front of any
translator or chatbot and recovers **98%** of the lost meaning on held-out everyday sentences
(86% vs. 54% for a dictionary baseline on messy, unseen spellings).

![main result](figures/main_test_tatoeba.png)

* **Notebook with all results:** [`Qalaisyn.ipynb`](Qalaisyn.ipynb)
* **One-page write-up:** [`WRITEUP.md`](WRITEUP.md) / `WRITEUP.pdf`

## Repository
| Path | What it is |
|---|---|
| `src/chatify.py` | simulates four chat typing styles, typos and unseen spellings |
| `src/build_data.py` | builds training text and held-out test sets |
| `src/restore.py` | B1 rules, B2 dictionary, M1/M2 Qalaisyn (candidates + habit model + bigram LM + Viterbi + char 5-gram + typo search) |
| `src/eval_restore.py`, `src/stress.py` | word/char error rates, stress tests |
| `src/eval_translate.py` | NLLB-200 translation + chrF |
| `src/analysis.py`, `src/charts.py` | failure analysis and figures |
| `src/app.py` | Gradio demo |

## Reproduce
```bash
pip install numpy pandas scikit-learn sacrebleu matplotlib pyarrow torch transformers==4.46.3 sentencepiece gradio==5.9.1
# download raw data: see the setup cell in Qalaisyn.ipynb
python src/build_data.py
python src/eval_restore.py test_tatoeba && python src/eval_restore.py test_flores
python src/stress.py test_tatoeba && python src/stress.py test_flores
python src/eval_translate.py test_tatoeba test_flores test_tatoeba_typos-5 test_tatoeba_typos-15 test_tatoeba_unseen-habits test_flores_typos-15 test_flores_unseen-habits
python src/analysis.py && python src/charts.py
python src/app.py --share
```

*Prototype. Not for medical, financial or emergency use.* Sources and licences: see `WRITEUP.md`.
