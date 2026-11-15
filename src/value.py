"""Why a model and not just a dictionary?  Four answers, each with a 95% bootstrap confidence interval.

1. Whole messages: share of messages restored with no mistake at all (what a chatbot actually needs).
2. Word errors: Qalaisyn vs. dictionary, and how many of the dictionary's mistakes Qalaisyn fixes vs. breaks.
3. Messy messages (typos): meaning recovered.
4. Knowing when it is unsure (see confidence.py) - a dictionary cannot do this at all.
Bootstrap: resample messages with replacement 1000 times; report the 2.5-97.5 percentile of the difference."""
import json
import random
import sys
from pathlib import Path

import sacrebleu

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
M, D = "M2 Qalaisyn+typos", "B2 dictionary"
B = 1000


def rows(name, kind="restored"):
    return [json.loads(l) for l in open(P / f"{kind}_{name}.jsonl", encoding="utf-8")]


sys.path.insert(0, str(Path(__file__).parent))
from eval_restore import wer as word_errors  # noqa: E402  (same edit-distance WER as everywhere else)


def ci(values):
    v = sorted(values)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]


def message_level(data, rng):
    # per-message numbers computed once; the bootstrap only re-sums them
    okm_l = [r[M] == r["gold"] for r in data]
    okd_l = [r[D] == r["gold"] for r in data]
    em_l, n_l = zip(*[word_errors(r[M], r["gold"]) for r in data])
    ed_l = [word_errors(r[D], r["gold"])[0] for r in data]

    def stats(idx):
        n = sum(n_l[i] for i in idx)
        return (sum(okm_l[i] for i in idx) / len(idx), sum(okd_l[i] for i in idx) / len(idx),
                sum(em_l[i] for i in idx) / n, sum(ed_l[i] for i in idx) / n)
    base = stats(range(len(data)))
    boots = [stats([rng.randrange(len(data)) for _ in data]) for _ in range(B)]
    raw = [word_errors(r["chat"], r["gold"]) for r in data]
    return {"messages_fully_right": {"qalaisyn": base[0], "dictionary": base[1],
                                     "diff_ci": ci([b[0] - b[1] for b in boots])},
            "word_error_rate": {"qalaisyn": base[2], "dictionary": base[3],
                                "as_typed": sum(a for a, _ in raw) / sum(n for _, n in raw),
                                "diff_ci": ci([b[2] - b[3] for b in boots])}}


def fixes_vs_breaks(data):
    fixed = broke = 0
    for r in data:
        g, m, d = r["gold"].split(), r[M].split(), r[D].split()
        if len(g) == len(m) == len(d):
            for a, b, c in zip(g, m, d):
                fixed += (c != a and b == a)
                broke += (c == a and b != a)
    return {"dictionary_mistakes_fixed": fixed, "new_mistakes": broke}


def chrf_diff(data, rng):
    refs = [r["eng"] for r in data]
    hm, hd = [r[f"en|{M}"] for r in data], [r[f"en|{D}"] for r in data]
    base = (sacrebleu.corpus_chrf(hm, [refs]).score, sacrebleu.corpus_chrf(hd, [refs]).score)
    diffs = []
    for _ in range(300):    # chrF is slower; 300 resamples are enough for a stable interval
        idx = [rng.randrange(len(data)) for _ in data]
        r = [refs[i] for i in idx]
        diffs.append(sacrebleu.corpus_chrf([hm[i] for i in idx], [r]).score
                     - sacrebleu.corpus_chrf([hd[i] for i in idx], [r]).score)
    return {"qalaisyn": base[0], "dictionary": base[1], "diff_ci": ci(diffs)}


if __name__ == "__main__":
    rng = random.Random(0)
    out = {}
    tests = {"Russian keyboard, everyday": "test_tatoeba_cyr", "Russian keyboard, news": "test_flores_cyr",
             "Latin chat, everyday": "test_tatoeba", "Russian keyboard + 15% typos": "test_tatoeba_cyr-typos-15",
             "Latin + 15% typos": "test_tatoeba_typos-15", "Latin, unseen spellings": "test_tatoeba_unseen-habits"}
    for label, name in tests.items():
        data = rows(name)
        res = message_level(data, rng)
        res.update(fixes_vs_breaks(data))
        tr = P / f"translated_{name}.jsonl"
        if tr.exists():
            res["chrf"] = chrf_diff(rows(name, "translated"), rng)
        out[label] = res
        mf = res["messages_fully_right"]
        print(f"{label:30s} fully right: {mf['qalaisyn']:.0%} vs {mf['dictionary']:.0%} "
              f"(diff CI {mf['diff_ci'][0]:+.1%}..{mf['diff_ci'][1]:+.1%}) | fixes {res['dictionary_mistakes_fixed']} "
              f"/ breaks {res['new_mistakes']}"
              + (f" | chrF {res['chrf']['qalaisyn']:.1f} vs {res['chrf']['dictionary']:.1f} "
                 f"(CI {res['chrf']['diff_ci'][0]:+.1f}..{res['chrf']['diff_ci'][1]:+.1f})" if "chrf" in res else ""))
    (ROOT / "results" / "value.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
