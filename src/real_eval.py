"""Real chat messages written by a native Kazakh speaker (a friend of the team, with permission):
for each everyday situation they wrote the message exactly as they would text it, and its correct spelling.
Never used for development or tuning.
Translation reference: the NLLB translation of the *correct* spelling (no English references exist for these
messages), i.e. we measure how much of the meaning of the correct text survives."""
import csv
import json
import re
import sys
from pathlib import Path

import sacrebleu

sys.path.insert(0, str(Path(__file__).parent))
from chatify import normalize_cyr  # noqa: E402
from eval_restore import evaluate, load_lexicon  # noqa: E402
from restore import DictRestorer, QalaisynRestorer, RuleRestorer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "real" / "ДЛЯ_ДРУГА.csv"   # columns: №, situation, hint, as typed, correct
THRESHOLD = 0.9


def as_typed(s: str) -> str:
    """What the restorer receives: lower case, punctuation removed (as in the demo)."""
    return " ".join(re.findall(r"[\w'-]+", s.lower()))


CYR_KZ = set("әғқңөұүһі")


def style_of(typed: str) -> str:
    if re.search(r"[a-z]", typed.lower()) and not re.search(r"[а-я]", typed.lower()):
        return "latin"
    if any(ch in CYR_KZ for ch in typed.lower()):
        return "partial-kazakh-keyboard"
    return "russian-keyboard"


def load_rows(path=CSV):
    rows = []
    if not Path(path).exists():
        return rows
    reader = csv.reader(open(path, encoding="utf-8-sig"))
    next(reader, None)
    for r in reader:
        if len(r) < 5 or not r[3].strip() or not r[4].strip():
            continue
        rows.append({"id": int(r[0]), "situation": r[1], "profile": style_of(r[3]), "kaz": r[4],
                     "gold": normalize_cyr(r[4]), "chat": as_typed(r[3])})
    return rows


def main():
    rows = load_rows()
    if not rows:
        print("No native-speaker messages filled in yet:", CSV)
        return
    lex = load_lexicon()
    m2 = QalaisynRestorer(lex, fuzzy=True, name="M2 Qalaisyn+typos")
    # the model exactly as it was when these messages were first tested (before the particle-harmony rule,
    # which was added after looking at these errors) - this is the truly held-out number
    m2_before = QalaisynRestorer(lex, fuzzy=True, harmony=False, name="M2 before native check")
    restorers = [RuleRestorer(), DictRestorer(lex), QalaisynRestorer(lex), m2_before, m2]
    table, outs = evaluate(restorers, rows, "real")
    # suggestions
    for o in outs:
        words = m2.restore_with_confidence(o["chat"])
        o["unsure"] = [{"typed": w["typed"], "ours": w["word"], "alts": w["alternatives"]}
                       for w in words if w["confidence"] < THRESHOLD]
    # translation
    from eval_translate import Translator
    tr = Translator()
    chrf = {}
    refs = tr.translate([o["gold"] for o in outs])      # meaning of the correct text
    for o, ref in zip(outs, refs):
        o["en|reference"] = ref
    for cond in ["B0 raw chat", "B2 dictionary", "M2 Qalaisyn+typos"]:
        hyps = tr.translate([o[cond] for o in outs])
        for o, h in zip(outs, hyps):
            o[f"en|{cond}"] = h
        chrf[cond] = sacrebleu.corpus_chrf(hyps, [refs]).score
    unsure_words = sum(len(o["unsure"]) for o in outs)
    total_words = sum(len(o["chat"].split()) for o in outs)
    res = {"n": len(rows), "wer": {k: v["WER"] for k, v in table.items()}, "chrf_vs_correct_translation": chrf,
           "unsure_share": unsure_words / max(1, total_words), "outputs": outs}
    (ROOT / "results" / "real.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rows)} native-speaker messages")
    for k, v in sorted(table.items()):
        print(f"  {k:34s} WER {v['WER']:.1%}")
    for k, v in chrf.items():
        print(f"  chrF {k:18s} {v:.1f}")
    print("\nmistakes of M2:")
    for o in outs:
        if o["M2 Qalaisyn+typos"] != o["gold"]:
            g, h = o["gold"].split(), o["M2 Qalaisyn+typos"].split()
            diff = [(a, b) for a, b in zip(g, h) if a != b] if len(g) == len(h) else [(o["gold"], o["M2 Qalaisyn+typos"])]
            flagged = {u["typed"] for u in o["unsure"]}
            print(f"  [{o['profile']}] {o['chat']}  ->  {diff}   unsure: {sorted(flagged)}")


if __name__ == "__main__":
    main()
