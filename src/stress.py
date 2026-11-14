"""Stress tests: where does Qalaisyn break?
  typos-5 / typos-15 : 5% / 15% of words get a thumb typo
  unseen-habits      : spellings the model was never designed for (ae, oe, kh, kk)
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from chatify import add_typos, chatify, chatify_unseen  # noqa: E402
from eval_restore import evaluate, load, load_lexicon  # noqa: E402
from restore import DictRestorer, QalaisynRestorer, RuleRestorer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def build(rows, kind):
    out = []
    if kind == "cyr-typos-15":     # Russian-keyboard Cyrillic + 15% thumb typos
        from chatify import chatify_cyr
        seen = set()
        for r in rows:
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            rr = dict(r)
            rr["chat"] = add_typos(chatify_cyr(r["kaz"], "ru-keyboard", random.Random(f"c-{r['id']}")), 0.15,
                                   random.Random(f"{kind}-{r['id']}"))
            rr["profile"] = kind
            out.append(rr)
        return out
    for r in rows:
        if r["profile"] != "typical" and kind != "unseen-habits":
            continue
        if kind == "unseen-habits" and r["profile"] != "minimal":
            continue
        rng = random.Random(f"{kind}-{r['id']}")
        rr = dict(r)
        if kind.startswith("typos"):
            rate = int(kind.split("-")[1]) / 100
            rr["chat"] = add_typos(chatify(r["kaz"], "typical", random.Random(f"t-{r['id']}")), rate, rng)
        else:
            rr["chat"] = chatify_unseen(r["kaz"], rng)
        rr["profile"] = kind
        out.append(rr)
    return out


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "test_tatoeba"
    lex = load_lexicon()
    restorers = [RuleRestorer(), DictRestorer(lex), QalaisynRestorer(lex),
                 QalaisynRestorer(lex, fuzzy=True, name="M2 Qalaisyn+typos")]
    base = load(name)
    results = {}
    for kind in ["typos-5", "typos-15", "unseen-habits", "cyr-typos-15"]:
        rows = build(base, kind)
        table, outs = evaluate(restorers, rows, f"{name}_{kind}")
        results[kind] = {k: v for k, v in table.items() if "|" not in k}
        print(kind, "  ".join(f"{k.split()[0]} WER {v['WER']:.3f}" for k, v in sorted(results[kind].items())))
        print("   e.g.", outs[3]["chat"], "->", outs[3]["M1 Qalaisyn"])
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / f"stress_{name}.json").write_text(json.dumps(results, indent=2))
