"""Does the method transfer? Same code, Kyrgyz data (Kyrgyz has ң, ө, ү like Kazakh).
Nothing is changed in the model; we only train it on Kyrgyz Wikipedia."""
import json
import random
import sys
from pathlib import Path

import pyarrow.parquet as pq
import sacrebleu

sys.path.insert(0, str(Path(__file__).parent))
from build_data import SENT_SPLIT, good_sentence  # noqa: E402
from chatify import chatify, normalize_cyr  # noqa: E402
from eval_restore import evaluate  # noqa: E402
from restore import DictRestorer, Lexicon, QalaisynRestorer, RuleRestorer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
N_TEST = 300


def main():
    fl = RAW / "flores200_dataset"
    kir = [l.rstrip("\n") for l in open(fl / "devtest/kir_Cyrl.devtest", encoding="utf-8")][:N_TEST]
    eng = [l.rstrip("\n") for l in open(fl / "devtest/eng_Latn.devtest", encoding="utf-8")][:N_TEST]
    test_norm = {normalize_cyr(k) for k in kir}

    sents, seen = [], set()
    for batch in pq.ParquetFile(RAW / "kywiki.parquet").iter_batches(columns=["text"], batch_size=2000):
        for doc in batch.column(0).to_pylist():
            for s in SENT_SPLIT.split(doc):
                s = s.strip()
                if good_sentence(s):
                    n = normalize_cyr(s)
                    if len(n.split()) >= 3 and n not in seen and n not in test_norm:
                        seen.add(n)
                        sents.append(n)
    print(f"Kyrgyz training sentences: {len(sents):,}")
    lex = Lexicon().fit(sents)
    restorers = [RuleRestorer(), DictRestorer(lex), QalaisynRestorer(lex),
                 QalaisynRestorer(lex, fuzzy=True, name="M2 Qalaisyn+typos")]

    rows = []
    for i, (k, e) in enumerate(zip(kir, eng)):
        for p in ["typical", "minimal"]:
            rows.append({"id": i, "profile": p, "kaz": k, "gold": normalize_cyr(k),
                         "chat": chatify(k, p, random.Random(f"ky-{i}-{p}")), "eng": e})
    table, outs = evaluate(restorers, rows, "kyrgyz")
    wer = {k: v["WER"] for k, v in table.items() if "|" not in k}
    for k, v in sorted(wer.items()):
        print(f"  {k:18s} WER {v:.3f}")

    from eval_translate import Translator
    tr = Translator(src="kir_Cyrl")
    chrf = {}
    for cond in ["gold", "B0 raw chat", "B2 dictionary", "M2 Qalaisyn+typos"]:
        hyps = tr.translate([o[cond] for o in outs])
        chrf[cond] = sacrebleu.corpus_chrf(hyps, [[o["eng"] for o in outs]]).score
        print(f"  chrF {cond:18s} {chrf[cond]:.1f}")
    rec = (chrf["M2 Qalaisyn+typos"] - chrf["B0 raw chat"]) / (chrf["gold"] - chrf["B0 raw chat"])
    print(f"  recovered: {rec:.0%}")
    (ROOT / "results" / "kyrgyz.json").write_text(json.dumps(
        {"train_sentences": len(sents), "wer": wer, "chrf": chrf, "recovered": rec,
         "examples": [{"chat": o["chat"], "ours": o["M2 Qalaisyn+typos"], "gold": o["gold"]} for o in outs[:6]]},
        ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
