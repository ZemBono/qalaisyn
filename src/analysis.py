"""Where does Qalaisyn fail? Per-letter error rates and example failures."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
MODEL = "M2 Qalaisyn+typos"
LETTERS = "аәкқоөуұүіиыйнңгғхһ"


def rows(name):
    return [json.loads(l) for l in open(P / f"restored_{name}.jsonl", encoding="utf-8")]


def letter_errors(data, model=MODEL):
    tot, err = Counter(), Counter()
    confusions = Counter()
    for r in data:
        g, h = r["gold"].split(), r[model].split()
        if len(g) != len(h):
            continue
        for gw, hw in zip(g, h):
            if len(gw) != len(hw):
                continue
            for a, b in zip(gw, hw):
                if a in LETTERS:
                    tot[a] += 1
                    if a != b:
                        err[a] += 1
                        confusions[(a, b)] += 1
    return {l: (err[l] / tot[l] if tot[l] else 0.0, tot[l]) for l in LETTERS}, confusions


def failures(data, model=MODEL, n=12):
    out = []
    for r in data:
        g, h = r["gold"].split(), r[model].split()
        if len(g) == len(h):
            wrong = [(gw, hw) for gw, hw in zip(g, h) if gw != hw]
            if wrong:
                out.append({"chat": r["chat"], "ours": r[model], "gold": r["gold"], "wrong": wrong,
                            "profile": r["profile"]})
    return out[:n]


def by_length(data, model=MODEL):
    buckets = defaultdict(lambda: [0, 0])
    for r in data:
        n = len(r["gold"].split())
        b = "1-4 words" if n <= 4 else "5-8 words" if n <= 8 else "9-15 words" if n <= 15 else "16+ words"
        g, h = r["gold"].split(), r[model].split()
        e = sum(a != b2 for a, b2 in zip(g, h)) + abs(len(g) - len(h))
        buckets[b][0] += e
        buckets[b][1] += len(g)
    return {k: v[0] / v[1] for k, v in buckets.items()}


if __name__ == "__main__":
    data = rows("test_tatoeba") + rows("test_flores")
    rates, conf = letter_errors(data)
    print("Per-letter error rate (M2, clean test sets):")
    for l, (r, n) in sorted(rates.items(), key=lambda x: -x[1][0]):
        print(f"  {l}: {r:.2%}  (n={n})")
    print("Top confusions:", conf.most_common(10))
    print("By length:", by_length(data))
    for f in failures(rows("test_tatoeba"), n=10):
        print(" ", f["chat"], "|", f["wrong"])
    res = {"letters": {l: {"error_rate": r, "n": n} for l, (r, n) in rates.items()},
           "confusions": [[a, b, c] for (a, b), c in conf.most_common(20)],
           "by_length": by_length(data)}
    (ROOT / "results" / "analysis.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
