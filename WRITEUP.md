# Qalaisyn: making AI understand Kazakh the way people actually type

**Track:** Languages · **Team:** Zhasulan B.

## The problem
Most phones in Kazakhstan have a Russian keyboard, so people drop the Kazakh-only letters (ә ғ қ ң ө ұ ү һ і) and type *калайсын* instead of *қалайсың*; others text in Latin (*qalaisyn*). Translators and chatbots are trained on standard Kazakh. We measured the cost on held-out data: on a Russian keyboard **almost every second word (47%) is misspelled** and a translator loses about a quarter of the meaning; in Latin it loses **75%**. As banks, clinics and e-government services put AI first in line, people who type "the way their phone lets them" get worse help. The same happens in other languages whose letters get dropped on phones (Uzbek, Kyrgyz, Azerbaijani, Vietnamese…).

## What we built
**Qalaisyn** is not an app people download. It is a small AI layer that sits inside any chatbot, translator or keyboard, like autocorrect. **In:** *баламнын кызуы 39 котерилди не истеу керек*. **Out:** *баламның қызуы 39 көтерілді не істеу керек* ("my child's temperature rose to 39, what should I do"), which the AI now understands. When unsure, it **shows suggestions** (*ot* → **от** 73% · өт 27%) instead of silently guessing.
**User:** Gulnar, 62, from a village in Turkistan region, texting a clinic chatbot at night from a phone with only a Russian keyboard.

## What we added
Our own idea (not a suggested project). Our own data and questions: (1) a generator that simulates six real typing styles (Russian keyboard, partial Kazakh keyboard, four Latin styles), so we never need anyone's private chats; (2) stress tests that ask *when does it break?*; (3) calibrated confidence and suggestions; (4) a transfer test on Kyrgyz.

## How it works
**Data:** 1.5M Kazakh Wikipedia + 4k Tatoeba sentences for training. Held-out tests: 623 everyday Tatoeba and FLORES-200 news sentences, each with a professional English translation. Tuning on FLORES `dev` only; no test sentence was seen in training.
**Model:** For each typed word we list the Kazakh words it could be (к → к/қ, а → а/ә, и → и/і …). A typing-habit model and a **word-bigram language model** score them, and **Viterbi decoding** picks the most likely sentence. Unknown words go to a **character 5-gram model**, likely typos to a **one-edit neighbour search**. **Forward-backward** gives each word a probability, and words under 90% become suggestions. It runs in milliseconds on a laptop.

## Results (held-out test data; translator NLLB-200, chrF vs. professional English)
| | Proper text | As typed | Dictionary | **Qalaisyn** |
|---|---|---|---|---|
| Russian keyboard: words wrong | – | 46.9% | 5.1% | **3.6%** (2.2% without typo search) |
| Russian keyboard: translation chrF | 60.8 | 45.2 | 59.4 | **59.9** (recovers **94%** of lost meaning; dictionary 91%) |
| Russian keyboard + 15% typos: chrF | 60.8 | 36.0 | 52.6 | **57.6** (**87%** vs. 67%) |
| Latin chat: translation chrF | 60.8 | 15.3 | 58.4 | **59.9** (**98%** vs. 95%) |
| Latin, unseen spellings (ae, kk): chrF | 60.8 | 14.2 | 39.3 | **54.4** (**86%** vs. 54%) |

**Suggestions:** only **5% of words** are flagged, yet they contain **59% of all Qalaisyn's mistakes**, and for 75% of those the right word is among the suggestions. Words it is sure about are wrong only 1.4% of the time.
**Transfer:** the same code trained on Kyrgyz Wikipedia recovers **97%** of the lost meaning for Kyrgyz.
**Honest notes:** on clean text a simple dictionary is close; Qalaisyn's advantage is on real, messy messages and in knowing when it is unsure. **Where it fails:** н/ң and і/и when both words exist, and true ambiguity (*ot* = от "fire" / өт "pass"). Some "errors" are typos in the reference (*қагаз*, *сатыл ал*) that Qalaisyn fixed.

## What we'd do next
1. Longer context (trigrams or a small neural re-ranker) for н/ң and і/и. 2. A keyboard and a plug-in API for public-service chatbots; more languages (Uzbek, Azerbaijani).

## Sources
Tatoeba (CC BY 2.0 FR) · FLORES-200 (CC BY-SA 4.0) · Kazakh and Kyrgyz Wikipedia via Hugging Face `wikimedia/wikipedia` (CC BY-SA) · NLLB-200 distilled 600M, Meta (CC BY-NC 4.0, evaluation only) · PyTorch, Transformers, sacrebleu, pandas, matplotlib, Gradio · Claude (Anthropic) helped write code and text.
*This project is a prototype and is not medical or financial advice.*
