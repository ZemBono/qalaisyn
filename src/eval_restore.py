"""Train the lexicon/LM and measure restoration quality (word error rate, char error rate)."""
import json
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from restore import DictRestorer, Lexicon, QalaisynRestorer, RuleRestorer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "lexicon.pkl"


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def wer(hyp, ref):
    r = ref.split()
    return edit_distance(hyp.split(), r), len(r)


def cer(hyp, ref):
    return edit_distance(hyp, ref), len(ref)


def load_lexicon(max_wiki=None, tatoeba_weight=20):
    if CACHE.exists() and max_wiki is None:
        with open(CACHE, "rb") as f:
            return pickle.load(f)
    t = time.time()
    wiki = (P / "train_wiki.txt").read_text(encoding="utf-8").split("\n")
    if max_wiki:
        wiki = wiki[:max_wiki]
    tat = (P / "train_tatoeba.txt").read_text(encoding="utf-8").split("\n")
    lex = Lexicon().fit(wiki + tat, [1] * len(wiki) + [tatoeba_weight] * len(tat))
    print(f"lexicon: {len(lex.uni):,} words, {len(lex.bi):,} bigrams, {time.time() - t:.0f}s")
    if max_wiki is None:
        with open(CACHE, "wb") as f:
            pickle.dump(lex, f, protocol=pickle.HIGHEST_PROTOCOL)
    return lex


def load(name):
    return [json.loads(l) for l in open(P / f"{name}.jsonl", encoding="utf-8")]


def evaluate(restorers, rows, out_name=None):
    stats = defaultdict(lambda: [0, 0, 0, 0])
    outputs = []
    for r in rows:
        rec = dict(r)
        for res in restorers + ["B0 raw chat"]:
            name = res if isinstance(res, str) else res.name
            hyp = r["chat"] if isinstance(res, str) else res.restore(r["chat"])
            rec[name] = hyp
            we, wn = wer(hyp, r["gold"])
            ce, cn = cer(hyp, r["gold"])
            for key in (name, f"{name}|{r['profile']}"):
                s = stats[key]
                s[0] += we; s[1] += wn; s[2] += ce; s[3] += cn
        outputs.append(rec)
    if out_name:
        with open(P / f"restored_{out_name}.jsonl", "w", encoding="utf-8") as f:
            for o in outputs:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")
    table = {k: {"WER": v[0] / v[1], "CER": v[2] / v[3]} for k, v in stats.items()}
    return table, outputs


if __name__ == "__main__":
    lex = load_lexicon()
    restorers = [RuleRestorer(), DictRestorer(lex), QalaisynRestorer(lex),
                 QalaisynRestorer(lex, fuzzy=True, name="M2 Qalaisyn+typos")]
    which = sys.argv[1] if len(sys.argv) > 1 else "dev_flores"
    rows = load(which)
    t = time.time()
    table, _ = evaluate(restorers, rows, which)
    print(f"{which}: {len(rows)} messages, {time.time() - t:.0f}s")
    for k in sorted(table):
        if "|" not in k:
            print(f"  {k:16s} WER {table[k]['WER']:.3f}  CER {table[k]['CER']:.3f}")
    for k in sorted(table):
        if "|" in k:
            print(f"  {k:28s} WER {table[k]['WER']:.3f}")
