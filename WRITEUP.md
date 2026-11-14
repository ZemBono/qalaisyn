# Qalaisyn: making AI understand Kazakh the way people actually text

**Track:** Languages · **Team:** Zhasulan B.

## The problem
Most Kazakhs text in Latin letters and drop the special Kazakh letters (ә, ғ, қ, ң, ө, ұ, ү, і): *"qalaisyn"* instead of *"қалайсың"*. Translators and chatbots are trained on standard Cyrillic Kazakh. We measured what that costs: **a translator loses 75% of the meaning** of chat-style Kazakh (chrF 60.8 → 15.3). As banks, clinics and e-government services put AI first in line, people who write "the way they text" get worse help, or none. The same problem affects other languages whose special letters get dropped on phones (Uzbek, Kyrgyz, Azerbaijani, Vietnamese, Yoruba…).

## What we built
**Qalaisyn** is a small AI layer that sits in front of any translator or chatbot. **In:** a chat-style message such as *balamnyn qyzuy 39 koterildi ne isteu kerek*. **Out:** standard Kazakh, *баламның қызуы 39 көтерілді не істеу керек* ("my child's temperature rose to 39, what should I do"), which the AI can now understand.
**User:** Gulnar, 62, from a village in Turkistan region. Her phone has no Kazakh keyboard, and she texts a clinic chatbot at night.

## What we added
Our own idea (not a suggested project). Our own data and question: (1) a generator that simulates four real typing styles, so we never need anyone's private chats; (2) stress tests that ask *when does it break?* (typos and spellings the model was never designed for); (3) real messages written and corrected by a native speaker.

## How it works
**Data:** 1.5M sentences from Kazakh Wikipedia and 4k from Tatoeba for training. Held-out tests: 623 everyday Tatoeba sentences and FLORES-200 news sentences, each with a professional English translation, turned into 4 chat styles. Tuning used only FLORES `dev`; no test sentence was seen in training.
**Model:** For every chat word we generate the Kazakh words it could be (`k` → к/қ, `a` → а/ә, `i` → і/и/ы …). A typing-habit model (a writer who uses `q` for қ probably means к by `k`) and a **word-bigram language model** score them, and **Viterbi decoding** picks the most likely sentence. Unknown words are restored with a **character 5-gram model**, and probable typos with a **one-edit neighbour search**. It runs in milliseconds on a laptop, and every decision can be explained.

## Results (held-out test data)
| | Proper text | Chat as typed | Letter rules | Dictionary | **Qalaisyn** |
|---|---|---|---|---|---|
| Translation chrF, everyday | 60.8 | 15.3 | 41.5 | 58.4 | **59.9** (recovers **98%** of lost meaning) |
| Translation chrF, news | 52.7 | 20.1 | 39.8 | 51.9 | **51.8** (97%) |
| Word errors, everyday | – | 99.9% | 47.6% | 5.4% | **3.8%** (2.3% without typo search) |
| **Messy:** 15% typos, chrF | 60.8 | 14.2 | 37.1 | 53.3 | **57.0** (92% vs. 84%) |
| **Messy:** unseen spellings, chrF | 60.8 | 14.2 | 31.4 | 39.3 | **54.4** (86% vs. 54%) |

**Honest notes.** On clean news text, a simple dictionary is already as good as our model. Our advantage appears on everyday and messy messages, which is what real chats look like. Typo search costs about 1.5 points of word errors on perfectly clean text; we accept that cost because it adds 15 chrF points on unseen spellings.
**Where it fails:** н/ң and і/ы/и (both choices are often real words, and a bigram has short memory), and true ambiguity like *ot* = от "fire" / өт "pass". Some "errors" are actually typos in the reference (*қагаз*, *сатыл ал*), which Qalaisyn fixed to *қағаз*, *сатып ал*, so our scores are slightly pessimistic.
**Native-speaker check:** see notebook section 9.

## What we'd do next
1. Use longer context (trigrams or a small neural re-ranker) for н/ң and і/ы/и.
2. Port the method to Kyrgyz and Uzbek (only the letter table changes) and offer it as a plug-in for public-service chatbots.

## Sources
Tatoeba (CC BY 2.0 FR) · FLORES-200 (CC BY-SA 4.0) · Kazakh Wikipedia via Hugging Face `wikimedia/wikipedia` (CC BY-SA) · NLLB-200 distilled 600M, Meta (CC BY-NC 4.0, evaluation only) · PyTorch, Hugging Face Transformers, sacrebleu, pandas, matplotlib, Gradio · Claude (Anthropic) helped write code and text.
*This project is a prototype and is not medical or financial advice.*
