# Сценарий видео (до 2 минут, на английском)

Запись экрана + твой голос. Открыть заранее: демо-страницу (`python src/app.py`, Claude поможет запустить) и ноутбук с графиками.
Говори спокойно, можно читать с листа. Ниже русский перевод для понимания.

---

### 0:00–0:15 · Problem (на экране: сообщение латиницей)
> "Imagine a grandmother in a Kazakh village texting a clinic chatbot at night on a phone with a Russian keyboard: *баламнын кызуы 39 котерилди*. Any Kazakh person understands it. AI often doesn't, because it learned only 'proper' Kazakh with letters like қ, ң, ө — and most phones can't easily type them."

*(Представьте бабушку из аула, которая ночью пишет в чат-бот поликлиники с телефона с русской раскладкой. Любой казах поймёт. ИИ часто нет: он учился на «правильном» казахском с буквами қ, ң, ө, а на большинстве телефонов их неудобно набирать.)*

### 0:15–1:15 · Demo (на экране: демо-страница)
1. Вставить пример 1 (температура) → нажать Translate.
> "On the left is what a translator gives you from the message as typed. It's nonsense. In the middle, Qalaisyn restores the Kazakh letters; the highlighted ones are what it fixed. On the right, the AI understands again: *my child's temperature rose to 39, what should I do?*"
2. Пример про карту/деньги.
> "Same thing for money: *money disappeared from my card*."
3. Набрать своё сообщение вживую, как пишешь другу.
> "And here's a message I just typed the way I text my friends."

### 1:15–1:45 · How it works and results (на экране: главный график, потом график с опечатками)
> "Qalaisyn guesses which Kazakh word each chat word could be and uses a language model trained on 1.5 million sentences to pick the most likely sentence. On held-out test data, a translator loses 75% of the meaning of chat-style Kazakh. Qalaisyn recovers 98% of it. A simple dictionary does almost as well on clean text, but on messy messages with spellings it has never seen, the dictionary recovers 54% and Qalaisyn 86%."

### 1:45–2:00 · Limitation and next steps
> "It still mixes up н and ң when both are real words. Next, we want longer context and to bring the same idea to Kyrgyz and Uzbek, so nobody gets worse help from AI just because of how they type."

---
**Советы:** закрой лишние вкладки; увеличь масштаб страницы (Ctrl +); перед записью проверь, что демо открыто и примеры работают.
