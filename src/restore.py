"""Restore standard Cyrillic Kazakh from chat-style Latin Kazakh.

Three restorers, from simplest to ours:
  B1  RuleRestorer        - every Latin letter -> its most common Cyrillic letter
  B2  DictRestorer        - every word -> its most frequent matching Kazakh word
  M1  QalaisynRestorer    - candidate words + typing-habit channel model
                            + word n-gram language model (Viterbi over the sentence)
                            + character n-gram model for unknown words
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

# ---------------------------------------------------------------- canonical keys
# Every Cyrillic letter is reduced to a "skeleton" letter. Words that look the
# same once the special Kazakh letters are stripped share a skeleton.
CANON = {
    "а": "a", "ә": "a", "б": "b", "в": "v", "г": "g", "ғ": "g", "д": "d", "е": "e",
    "э": "e", "ж": "j", "з": "z", "и": "i", "й": "i", "і": "i", "ы": "i", "к": "k",
    "қ": "k", "л": "l", "м": "m", "н": "n", "ң": "n", "о": "o", "ө": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ұ": "u", "ү": "u", "ф": "f", "х": "h",
    "һ": "h", "ц": "c", "ч": "C", "ш": "S", "щ": "S", "ъ": "", "ь": "", "ю": "iu",
    "я": "ia", "ё": "io", "-": "-",
}


def canon_word(word: str) -> str:
    return "".join(CANON.get(ch, ch) for ch in word)


# Chat-side parsing: each position may be read in several ways.
_MULTI = [
    ("sh", ["S"]), ("zh", ["j"]), ("ch", ["C"]), ("gh", ["g"]),
    ("ts", ["c", "ts"]), ("ng", ["n", "ng"]),
]
_SINGLE = {
    "q": ["k"], "ä": ["a"], "ö": ["o"], "ü": ["u"], "ı": ["i"], "y": ["i"],
    "ğ": ["g"], "ñ": ["n"], "ş": ["S"], "x": ["h"], "w": ["S", "u", "v"],
    "c": ["c", "C", "s"], "j": ["j"],
}
# Latin markers that can only come from one special Kazakh letter.
STRICT = {"q": "қ", "ä": "ә", "ö": "ө", "ü": "ү", "ğ": "ғ", "ñ": "ң", "ı": "ы", "ş": "ш"}


def clean_token(tok: str) -> str:
    return re.sub(r"['`’]", "", tok.lower())


def chat_variants(tok: str, limit: int = 32) -> list[str]:
    tok = clean_token(tok)
    results = [""]
    i = 0
    while i < len(tok):
        opts = None
        for pat, outs in _MULTI:
            if tok.startswith(pat, i):
                opts, step = outs, len(pat)
                break
        if opts is None:
            ch = tok[i]
            opts, step = _SINGLE.get(ch, [ch]), 1
        results = [r + o for r in results for o in opts][:limit]
        i += step
    return results


# ---------------------------------------------------------------- B1: rules
RULE_MULTI = [("sh", "ш"), ("zh", "ж"), ("ch", "ч"), ("gh", "ғ"), ("ts", "ц"),
              ("yu", "ю"), ("ya", "я"), ("yo", "ё"), ("ng", "ң")]
RULE_SINGLE = {
    "a": "а", "b": "б", "c": "ц", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "х",
    "i": "і", "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
    "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "w": "у", "x": "х",
    "y": "ы", "z": "з", "ä": "ә", "ö": "ө", "ü": "ү", "ğ": "ғ", "ñ": "ң", "ı": "ы", "ş": "ш",
}


def rule_word(tok: str) -> str:
    tok = clean_token(tok)
    if tok.isdigit():
        return tok
    out, i = [], 0
    while i < len(tok):
        for pat, cyr in RULE_MULTI:
            if tok.startswith(pat, i):
                out.append(cyr)
                i += len(pat)
                break
        else:
            out.append(RULE_SINGLE.get(tok[i], tok[i]))
            i += 1
    return "".join(out)


class RuleRestorer:
    name = "B1 rules"

    def restore(self, text: str) -> str:
        return " ".join(rule_word(t) for t in text.split())


# ---------------------------------------------------------------- shared lexicon
def strict_ok(tok: str, word: str) -> bool:
    """A chat token with 'q' must come from a word with at least that many 'қ', etc."""
    t = clean_token(tok)
    for lat, cyr in STRICT.items():
        if t.count(lat) > word.count(cyr):
            return False
    return True


class Lexicon:
    def __init__(self):
        self.uni = Counter()
        self.bi = Counter()
        self.ctx = Counter()           # number of tokens following a word
        self.followers = Counter()     # distinct followers (Witten-Bell)
        self.by_key = defaultdict(list)
        self.total = 0
        self.char = None

    def fit(self, sentences, weights=None):
        weights = weights or [1] * len(sentences)
        for sent, w in zip(sentences, weights):
            words = ["<s>"] + sent.split() + ["</s>"]
            for a, b in zip(words, words[1:]):
                self.uni[b] += w
                if self.bi[(a, b)] == 0:
                    self.followers[a] += 1
                self.bi[(a, b)] += w
                self.ctx[a] += w
        self.total = sum(self.uni.values())
        for word, c in self.uni.items():
            if word in ("</s>",) or word.isdigit():
                continue
            self.by_key[canon_word(word)].append((c, word))
        for k in self.by_key:
            self.by_key[k].sort(reverse=True)
        self.char = CharLM(order=5).fit(self.uni)
        return self

    def p_uni(self, w):
        return (self.uni.get(w, 0) + 0.1) / (self.total + 0.1 * (len(self.uni) + 1))

    def logp(self, w, prev):
        """Interpolated bigram (Witten-Bell)."""
        pu = self.p_uni(w)
        c_prev = self.ctx.get(prev, 0)
        if c_prev == 0:
            return math.log(pu)
        t = self.followers[prev]
        lam = c_prev / (c_prev + t)
        return math.log(lam * self.bi.get((prev, w), 0) / c_prev + (1 - lam) * pu)

    def candidates(self, tok, top=25):
        seen = {}
        for key in chat_variants(tok):
            for c, w in self.by_key.get(key, [])[:top]:
                if strict_ok(tok, w):
                    seen[w] = max(seen.get(w, 0), c)
        return sorted(seen, key=seen.get, reverse=True)[:top]

    # ---- typo tolerance: words one edit away (symmetric-delete index)
    def build_fuzzy(self, min_count=3):
        self.del_index = defaultdict(set)
        for key, lst in self.by_key.items():
            if lst[0][0] < min_count or len(key) < 4:
                continue
            for i in range(len(key)):
                self.del_index[key[:i] + key[i + 1:]].add(key)
        return self

    def fuzzy_candidates(self, tok, top=10):
        if not hasattr(self, "del_index"):
            return []
        found = {}
        for v in chat_variants(tok, limit=8):
            if len(v) < 4:
                continue
            dels = {v[:i] + v[i + 1:] for i in range(len(v))}
            keys = set(self.del_index.get(v, ()))            # input lost a letter
            for d in dels:
                if d in self.by_key:                          # input has an extra letter
                    keys.add(d)
                keys |= self.del_index.get(d, set())          # swapped / substituted letter
            keys.discard(v)
            for k in keys:
                for c, w in self.by_key[k][:3]:
                    if strict_ok(tok, w):
                        found[w] = max(found.get(w, 0), c)
        return sorted(found, key=found.get, reverse=True)[:top]


# ---------------------------------------------------------------- character LM
# Which Cyrillic letters a skeleton letter can stand for.
CHAR_OPTS = {
    "a": "аә", "k": "кқ", "o": "оө", "u": "уұү", "i": "іиыйю", "n": "нң", "g": "гғ",
    "h": "хһ", "e": "еэ", "S": "шщ", "j": "ж", "C": "ч", "c": "цс", "b": "б", "v": "в",
    "d": "д", "z": "з", "l": "л", "m": "м", "p": "п", "r": "р", "s": "с", "t": "т",
    "f": "ф", "-": "-",
}
STRICT_SKEL = {"q": "қ", "ä": "ә", "ö": "ө", "ü": "ү", "ğ": "ғ", "ñ": "ң", "ı": "ы", "ş": "ш"}


class CharLM:
    def __init__(self, order=5):
        self.n = order
        self.counts = Counter()
        self.ctx = Counter()

    def fit(self, word_counts):
        for w, c in word_counts.items():
            if not w or w in ("<s>", "</s>") or w.isdigit():
                continue
            s = "^" * (self.n - 1) + w + "$"
            for i in range(self.n - 1, len(s)):
                for k in range(1, self.n + 1):
                    gram = s[i - k + 1:i + 1]
                    self.counts[gram] += c
                    self.ctx[gram[:-1]] += c
        return self

    def logp(self, history, ch):
        """Stupid backoff, good enough for ranking."""
        alpha = 0.0
        for k in range(self.n - 1, -1, -1):
            h = history[-k:] if k else ""
            c = self.counts.get(h + ch, 0)
            if c:
                return alpha + math.log(c / self.ctx[h])
            alpha += math.log(0.4)
        return alpha + math.log(1e-6)

    def restore(self, tok, beam=16):
        t = clean_token(tok)
        # parse into slots, each slot = list of cyrillic options (may be multi-char)
        slots, i = [], 0
        while i < len(t):
            two = t[i:i + 2]
            if two in ("sh", "zh", "ch", "gh"):
                slots.append({"sh": ["ш"], "zh": ["ж"], "ch": ["ч"], "gh": ["ғ"]}[two])
                i += 2
                continue
            if two in ("yu", "iu"):
                slots.append(["ю", "иу", "ыу", "йу", "іу"])
                i += 2
                continue
            if two in ("ya", "ia"):
                slots.append(["я", "иа", "ыа", "йа"])
                i += 2
                continue
            if two == "ng":
                slots.append(["ң", "нг"])
                i += 2
                continue
            ch = t[i]
            if ch in STRICT_SKEL:
                slots.append([STRICT_SKEL[ch]])
            elif ch == "y":
                slots.append(["ы", "й", "и"])
            elif ch == "w":
                slots.append(["ш", "у"])
            elif ch == "x":
                slots.append(["х", "һ"])
            elif ch in CHAR_OPTS:
                slots.append(list(CHAR_OPTS[ch]))
            else:
                slots.append([ch])
            i += 1
        hyps = [("^" * (self.n - 1), 0.0)]
        for opts in slots:
            new = []
            for h, s in hyps:
                for o in opts:
                    sc, hh = s, h
                    for c in o:
                        sc += self.logp(hh, c)
                        hh += c
                    new.append((hh, sc))
            new.sort(key=lambda x: -x[1])
            hyps = new[:beam]
        best = max(hyps, key=lambda x: x[1] + self.logp(x[0], "$"))
        return best[0][self.n - 1:]


# ---------------------------------------------------------------- B2: dictionary
class DictRestorer:
    name = "B2 dictionary"

    def __init__(self, lex: Lexicon):
        self.lex = lex

    def restore(self, text: str) -> str:
        out = []
        for tok in text.split():
            if tok.isdigit():
                out.append(tok)
                continue
            cands = self.lex.candidates(tok, top=1)
            out.append(cands[0] if cands else rule_word(tok))
        return " ".join(out)


# ---------------------------------------------------------------- M1: Qalaisyn
class QalaisynRestorer:
    name = "M1 Qalaisyn"

    def __init__(self, lex: Lexicon, habit_penalty=math.log(0.1), oov_penalty=-12.0,
                 top=25, use_char=True, fuzzy=False, typo_penalty=math.log(0.002),
                 name=None, fuzzy_below=5, char_bonus=0.0):
        # defaults for fuzzy_below / typo_penalty / char_bonus were tuned on FLORES dev only
        self.char_bonus = char_bonus
        self.fuzzy_below = fuzzy_below   # look for typo neighbours only if the word is unknown/rare
        self.lex = lex
        self.habit_penalty = habit_penalty
        self.oov_penalty = oov_penalty
        self.top = top
        self.use_char = use_char
        self.fuzzy = fuzzy
        self.typo_penalty = typo_penalty
        if name:
            self.name = name
        if fuzzy and not hasattr(lex, "del_index"):
            lex.build_fuzzy()

    def _channel(self, tok, word, uses_q):
        """Typing-habit model: if this writer uses 'q' for қ, a plain 'k' is probably к."""
        if not uses_q:
            return 0.0
        t = clean_token(tok)
        extra_q = word.count("қ") - t.count("q")
        return self.habit_penalty * max(0, extra_q)

    def restore(self, text: str, explain: bool = False):
        toks = text.split()
        if not toks:
            return ""
        uses_q = "q" in text.lower()
        lattice = []
        for tok in toks:
            if tok.isdigit():
                lattice.append([(tok, 0.0)])
                continue
            cands = self.lex.candidates(tok, self.top)
            opts = [(w, self._channel(tok, w, uses_q)) for w in cands]
            best_count = self.lex.uni.get(cands[0], 0) if cands else 0
            if self.fuzzy and len(tok) >= 4 and best_count < self.fuzzy_below:
                have = set(cands)
                fz = [w for w in self.lex.fuzzy_candidates(tok) if w not in have]
                for w in fz:
                    opts.append((w, self.typo_penalty + self._channel(tok, w, uses_q)))
                if fz and not cands:
                    # keep the letter-by-letter guess in the race (rare names, new words)
                    opts.append((self.lex.char.restore(tok), self.char_bonus))
            if not opts:
                guess = self.lex.char.restore(tok) if self.use_char else rule_word(tok)
                opts = [(guess, self.oov_penalty)]
            lattice.append(opts)
        # Viterbi over candidate words with the bigram LM
        best = {"<s>": (0.0, [])}
        for opts in lattice:
            new = {}
            for w, ch_score in opts:
                cand_best = None
                for prev, (s, path) in best.items():
                    sc = s + ch_score + self.lex.logp(w, prev)
                    if cand_best is None or sc > cand_best[0]:
                        cand_best = (sc, path + [w])
                new[w] = cand_best
            best = new
        final = max(best.items(), key=lambda kv: kv[1][0] + self.lex.logp("</s>", kv[0]))
        words = final[1][1]
        return " ".join(words)
