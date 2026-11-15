# Qalaisyn: an engine that lets AI understand Kazakh the way people really type it

**Track:** Languages · **Team:** Zhasulan B. · **Try it live (in your browser):** [zembono.github.io/qalaisyn/web](https://zembono.github.io/qalaisyn/web/) · **Code:** [github.com/ZemBono/qalaisyn](https://github.com/ZemBono/qalaisyn)

## The problem
Most phones in Kazakhstan have a Russian keyboard with no keys for the Kazakh letters ә ғ қ ң ө ұ ү һ і, so people type the closest Russian letter: *калайсын* for *қалайсың*. One letter can change the meaning: *өт* "go through" becomes *от* "fire". In our tests almost every second word typed this way is misspelled, and the AI that now answers bank, airline, clinic and government chats misreads it. An airline bot's translator reads *ушак кешигип жатыр ма* ("is the plane late?") as "is there a rumor going on?". A bank bot asked *несие бойынша толемди кешиктирсем бола ма* ("can I delay my loan payment?") explains how to withdraw cash.

## What we built
**Qalaisyn is an engine that works inside other systems:** it sits in a company's system, between the incoming message and the AI that answers it, like a spell-checker inside a keyboard. **In:** *баламнын кызуы 39 котерилди не истеу керек*. **Out:** *баламның қызуы 39 көтерілді не істеу керек* ("my child's temperature rose to 39, what should I do"), in Cyrillic or the new official Latin alphabet. When it is unsure it **shows suggestions** (*от* 73% · *өт* 27%) instead of guessing silently. It handles Russian-keyboard and Latin typing, leaves Russian words alone, and runs in about 7 ms per message (1.3 GB of memory). It also runs as a **browser extension**: Alt+Q in any text field, e.g. Google Translate.
**User:** Gulnar, 62, from a village in Turkistan region, texting a clinic chatbot at night from a phone with only a Russian keyboard.

## What we added
Our own data and questions: a generator of six real typing styles, 70 real messages written by a native speaker (one person, with permission), stress tests asking *when does it break?*, calibrated suggestions, a "why not a dictionary?" study with confidence intervals, and a transfer test on Kyrgyz.

## How it works
**Data:** 1.5M Kazakh Wikipedia sentences plus conversational text (Tatoeba, film subtitles). Held-out tests: 623 everyday and 300–1,012 news sentences (FLORES-200), each with a professional English translation, in six typing styles. Tuning on FLORES `dev` only. **Model:** each typed word → the Kazakh words it could be → a typing-habit model and a **word-bigram language model** score them → **Viterbi** picks the best sentence; a **character 5-gram model** handles unknown words, a one-edit search handles typos, and **forward-backward** gives each word a probability (below 90% → suggestion).

## Results (held-out test data, 95% bootstrap confidence intervals)
| | As typed | Dictionary | **Qalaisyn** |
|---|---|---|---|
| Russian keyboard: words wrong | 46.9% | 5.8% | **3.5%** |
| Russian keyboard: messages with every word right | – | 80% | **88%** (+9 pts, CI +7…+11) |
| Russian keyboard + 15% typos: messages fully right | – | 49% | **74%** (+25 pts, CI +21…+28) |
| Latin, unseen spellings: messages fully right | – | 19% | **58%** (+40 pts, CI +36…+43) |
| Meaning recovered for a translator, Russian keyboard + typos | 0% | 66% | **87%** |
| Words shown as suggestions · share of its mistakes among them | – | cannot tell | **6% · 62%** |
| **70 real messages by a native speaker** (slang, Russian words): words wrong | 61.4% | 20.1% | **15.0%** (16.1% before the last rule) |

**Why a model and not a dictionary?** A chatbot needs whole messages right; Qalaisyn fixes 154 of the dictionary's word mistakes for 38 new ones, wins by 21–40 points on messy messages, and knows when to ask. **Why not a large AI model?** It is paid per message, takes seconds and sends customers' messages to another company; Qalaisyn is free, takes milliseconds, runs on the company's own server and can sit in front of any AI (on the 70 native messages free ChatGPT leaves 12.9% of words wrong, Qalaisyn 15.0%: close, at a tiny fraction of the cost). **Prior work:** restoring dropped letters has been studied for languages such as Vietnamese and Romanian; new here is chat-style Kazakh (Russian keyboard or Latin, slang, Russian words, typos) with calibrated suggestions. **Honest notes:** on clean news text translation scores are equal (CI includes 0). Kyrgyz with the same code recovers 98% of the meaning in Latin and 86% on a Russian keyboard (where a dictionary is equally good). **Where it fails:** н/ң and і/и when both words exist, true ambiguity (*от*/*өт*), and some colloquial forms.

## What we'd do next
1. Expand shortened chat forms (*болад* → *болады*, *жберш* → *жіберші*), the main error left in the native-speaker messages, and longer context for н/ң and і/и. 2. A plug-in API for support chatbots and a phone keyboard; more languages.

## Sources
Tatoeba (CC BY 2.0 FR) · FLORES-200 (CC BY-SA 4.0) · Kazakh and Kyrgyz Wikipedia via Hugging Face (CC BY-SA) · OPUS OpenSubtitles · FrequencyWords Russian list (MIT/CC BY-SA) · NLLB-200 600M, Meta (CC BY-NC 4.0, evaluation only) · PyTorch, Transformers, sacrebleu, pandas, matplotlib, Gradio · Claude (Anthropic) helped with code and text.
*This project is a prototype and is not medical or financial advice.*
