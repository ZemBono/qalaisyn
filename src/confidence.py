"""Does Qalaisyn know when it might be wrong?
For every restored word we get a probability (forward-backward). Words below a threshold are
shown to the user as suggestions instead of being silently changed.
The threshold is chosen on FLORES dev; results are reported on held-out test sets."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from eval_restore import load, load_lexicon  # noqa: E402
from restore import QalaisynRestorer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def collect(q, rows):
    items = []   # (confidence, correct, gold_in_top3)
    for r in rows:
        res = q.restore_with_confidence(r["chat"])
        gold = r["gold"].split()
        if len(res) != len(gold):
            continue
        for x, g in zip(res, gold):
            if g.isdigit():
                continue
            items.append((x["confidence"], x["word"] == g, any(a == g for a, _ in x["alternatives"])))
    return items


def at_threshold(items, t):
    n = len(items)
    errors = [i for i in items if not i[1]]
    flagged = [i for i in items if i[0] < t]
    caught = [i for i in flagged if not i[1]]
    unflagged = [i for i in items if i[0] >= t]
    return {
        "threshold": t,
        "words": n,
        "error_rate": len(errors) / n,
        "flagged_share": len(flagged) / n,
        "errors_caught": len(caught) / max(1, len(errors)),
        "error_rate_unflagged": sum(1 for i in unflagged if not i[1]) / max(1, len(unflagged)),
        "fixed_by_top3_among_flagged_errors": sum(1 for i in caught if i[2]) / max(1, len(caught)),
    }


def calibration(items, bins=(0, .5, .7, .9, .99, 1.01)):
    out = []
    for lo, hi in zip(bins, bins[1:]):
        b = [i for i in items if lo <= i[0] < hi]
        if b:
            out.append({"confidence": f"{lo:.2f}-{min(hi, 1):.2f}", "words": len(b),
                        "actually_correct": sum(i[1] for i in b) / len(b)})
    return out


if __name__ == "__main__":
    q = QalaisynRestorer(load_lexicon(), fuzzy=True)
    dev = collect(q, load("dev_flores")[:1200] + load("dev_flores_cyr")[:800])
    # choose the threshold on dev: flag at most ~6% of words, catch as many errors as possible
    cands = [at_threshold(dev, t) for t in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)]
    ok = [c for c in cands if c["flagged_share"] <= 0.06]
    best = max(ok, key=lambda c: c["errors_caught"])["threshold"]
    print("dev candidates:", [(c["threshold"], round(c["flagged_share"], 3), round(c["errors_caught"], 2)) for c in cands])
    print("chosen threshold:", best)
    res = {"threshold": best}
    for name in ["test_tatoeba", "test_tatoeba_cyr", "test_flores_cyr"]:
        rows = load(name)
        if name == "test_flores_cyr":
            rows = rows[:800]
        items = collect(q, rows)
        res[name] = {"at_threshold": at_threshold(items, best), "calibration": calibration(items)}
        a = res[name]["at_threshold"]
        print(f"{name}: errors {a['error_rate']:.1%} | flagged {a['flagged_share']:.1%} of words | "
              f"caught {a['errors_caught']:.0%} of errors | error rate on unflagged {a['error_rate_unflagged']:.2%} | "
              f"right word in top-3 for {a['fixed_by_top3_among_flagged_errors']:.0%} of caught errors")
        print("   calibration:", res[name]["calibration"])
    (ROOT / "results" / "confidence.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
