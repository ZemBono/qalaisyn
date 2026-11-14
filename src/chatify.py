"""chatify: turn standard Cyrillic Kazakh into realistic chat-style Latin Kazakh.

Each simulated writer has a *profile* of typing habits (how they write қ, ә, ш ...).
This is how we create training/test pairs without collecting anyone's private messages.
"""
import random
import re

# For every Cyrillic letter: list of (latin_spelling, weight) per profile.
# Profiles:
#   careful   - uses q, ä, ö, ü, ğ, ñ (close to the official Latin alphabet)
#   typical   - q for қ, but drops other special letters (most common in chats)
#   minimal   - only plain ASCII, no q (k for both к and қ)
#   mixed     - typical + random variation between habits inside one message
BASE = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ә": "a", "ғ": "g", "қ": "k", "ң": "n", "ө": "o", "ұ": "u", "ү": "u",
    "һ": "h", "і": "i",
}

# Options per letter for each profile: list of (spelling, probability).
PROFILES = {
    "careful": {
        "қ": [("q", 1.0)], "ә": [("ä", 0.8), ("a", 0.2)], "ө": [("ö", 0.8), ("o", 0.2)],
        "ү": [("ü", 0.8), ("u", 0.2)], "ұ": [("u", 1.0)], "ғ": [("ğ", 0.5), ("g", 0.5)],
        "ң": [("ñ", 0.4), ("ng", 0.3), ("n", 0.3)], "і": [("i", 1.0)], "ы": [("y", 0.8), ("ı", 0.2)],
        "ш": [("sh", 0.7), ("ş", 0.3)], "ж": [("zh", 0.5), ("j", 0.5)], "х": [("h", 0.5), ("x", 0.5)],
        "й": [("i", 0.5), ("y", 0.5)], "у": [("u", 0.8), ("w", 0.2)], "ч": [("ch", 1.0)],
    },
    "typical": {
        "қ": [("q", 0.85), ("k", 0.15)], "ә": [("a", 0.9), ("ä", 0.1)], "ө": [("o", 1.0)],
        "ү": [("u", 1.0)], "ұ": [("u", 1.0)], "ғ": [("g", 0.85), ("gh", 0.15)],
        "ң": [("n", 0.7), ("ng", 0.3)], "і": [("i", 1.0)], "ы": [("y", 0.7), ("i", 0.3)],
        "ш": [("sh", 0.75), ("w", 0.25)], "ж": [("zh", 0.4), ("j", 0.6)], "х": [("h", 0.5), ("x", 0.5)],
        "й": [("i", 0.6), ("y", 0.4)], "у": [("u", 0.85), ("w", 0.15)], "ч": [("ch", 1.0)],
    },
    "minimal": {
        "қ": [("k", 1.0)], "ә": [("a", 1.0)], "ө": [("o", 1.0)], "ү": [("u", 1.0)],
        "ұ": [("u", 1.0)], "ғ": [("g", 1.0)], "ң": [("n", 1.0)], "і": [("i", 1.0)],
        "ы": [("i", 0.6), ("y", 0.4)], "ш": [("sh", 0.6), ("w", 0.4)], "ж": [("j", 0.7), ("zh", 0.3)],
        "х": [("h", 0.6), ("x", 0.4)], "й": [("i", 0.7), ("y", 0.3)], "у": [("u", 1.0)], "ч": [("ch", 1.0)],
    },
}
PROFILE_NAMES = ["careful", "typical", "minimal", "mixed"]

_word_re = re.compile(r"[а-яёәғқңөұүһі]+(?:-[а-яёәғқңөұүһі]+)*|\d+", re.IGNORECASE)


def normalize_cyr(text: str) -> str:
    """Gold format: lowercase Cyrillic words and numbers, no punctuation."""
    text = text.lower().replace("ё", "е")
    # common look-alike Latin letters inside Cyrillic text
    text = text.translate(str.maketrans({"i": "і", "a": "а", "o": "о", "e": "е", "c": "с", "p": "р"}))
    return " ".join(_word_re.findall(text))


def _pick(options, rng):
    r = rng.random()
    acc = 0.0
    for spelling, p in options:
        acc += p
        if r <= acc:
            return spelling
    return options[-1][0]


def chatify(text: str, profile: str = "typical", rng: random.Random | None = None) -> str:
    """Convert (already normalized) Cyrillic Kazakh into chat-style Latin."""
    rng = rng or random.Random(0)
    text = normalize_cyr(text)
    out = []
    # a writer keeps the same habit for a letter inside one message (more realistic)
    habits = {}
    for ch in text:
        prof = profile
        if profile == "mixed":
            prof = rng.choice(["careful", "typical", "minimal"])
            habit_key = ch + prof
        else:
            habit_key = ch
        table = PROFILES[prof]
        if ch in table:
            if habit_key not in habits or profile == "mixed":
                habits[habit_key] = _pick(table[ch], rng)
            out.append(habits[habit_key])
        elif ch in BASE:
            out.append(BASE[ch])
        else:
            out.append(ch)
    s = "".join(out)
    # chat noise: occasionally drop a hyphen, double a final letter for emphasis
    if rng.random() < 0.3:
        s = s.replace("-", " ")
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- Cyrillic chat styles
# The most common case in Kazakhstan: Cyrillic typed on a *Russian* keyboard, so the
# Kazakh-only letters are replaced by the closest Russian ones.
RU_KEYBOARD = {
    "ә": [("а", 1.0)], "ғ": [("г", 1.0)], "қ": [("к", 1.0)], "ң": [("н", 1.0)],
    "ө": [("о", 1.0)], "ұ": [("у", 1.0)], "ү": [("у", 1.0)], "һ": [("х", 1.0)],
    "і": [("и", 0.75), ("ы", 0.1), ("i", 0.15)],   # some type Latin i for і
}
CYR_PROFILES = ["ru-keyboard", "partial"]


def chatify_cyr(text: str, profile: str = "ru-keyboard", rng: random.Random | None = None) -> str:
    """Cyrillic chat style. ru-keyboard: every Kazakh letter replaced.
    partial: the writer has a Kazakh keyboard but keeps only some letters (per-letter habit)."""
    rng = rng or random.Random(0)
    text = normalize_cyr(text)
    keep = {ch: (profile == "partial" and rng.random() < 0.5) for ch in RU_KEYBOARD}
    habits, out = {}, []
    for ch in text:
        if ch in RU_KEYBOARD and not keep[ch]:
            if ch not in habits:
                habits[ch] = _pick(RU_KEYBOARD[ch], rng)
            out.append(habits[ch])
        else:
            out.append(ch)
    s = "".join(out)
    if rng.random() < 0.3:
        s = s.replace("-", " ")
    return re.sub(r"\s+", " ", s).strip()


UNSEEN = {"ә": "ae", "ө": "oe", "ү": "ue", "х": "kh", "қ": "kk", "ғ": "gg"}


def add_typos(chat: str, rate: float, rng: random.Random) -> str:
    """Realistic thumb typos: drop, double or swap letters in some words."""
    out = []
    for w in chat.split():
        if len(w) > 3 and not w.isdigit() and rng.random() < rate:
            i = rng.randrange(1, len(w) - 1)
            kind = rng.choice(["drop", "double", "swap"])
            if kind == "drop":
                w = w[:i] + w[i + 1:]
            elif kind == "double":
                w = w[:i] + w[i] + w[i:]
            else:
                w = w[:i] + w[i + 1] + w[i] + w[i + 2:]
        out.append(w)
    return " ".join(out)


def chatify_unseen(text: str, rng: random.Random) -> str:
    """A writer with habits the model was never told about (ae for ә, kh for х, kk for қ ...)."""
    text = normalize_cyr(text)
    s = "".join(UNSEEN.get(ch, PROFILES["minimal"].get(ch, [(BASE.get(ch, ch), 1)])[0][0]) for ch in text)
    return re.sub(r"\s+", " ", s).strip()


if __name__ == "__main__":
    demo = "Баламның қызуы 39 көтерілді, не істеу керек?"
    for p in PROFILE_NAMES:
        print(f"{p:8s} -> {chatify(demo, p, random.Random(1))}")
