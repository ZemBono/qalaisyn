"""Does the meaning survive? Translate every version with NLLB-200 and score chrF
against the professional English translation."""
import json
import sys
from collections import defaultdict
from pathlib import Path

import sacrebleu
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "translation_cache.jsonl"
MODEL = "facebook/nllb-200-distilled-600M"
CONDITIONS = ["gold", "B0 raw chat", "B1 rules", "B2 dictionary", "M1 Qalaisyn", "M2 Qalaisyn+typos"]


class Translator:
    def __init__(self, src="kaz_Cyrl", tgt="eng_Latn"):
        self.dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.tok = AutoTokenizer.from_pretrained(MODEL, src_lang=src)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL, torch_dtype=torch.float16 if self.dev == "cuda" else torch.float32).to(self.dev).eval()
        self.tgt_id = self.tok.convert_tokens_to_ids(tgt)
        self.cache = {}
        if CACHE.exists():
            for l in open(CACHE, encoding="utf-8"):
                d = json.loads(l)
                self.cache[d["src"]] = d["tgt"]

    @torch.no_grad()
    def translate(self, texts, batch=24):
        todo = sorted({t for t in texts if t not in self.cache}, key=len)
        with open(CACHE, "a", encoding="utf-8") as f:
            for i in range(0, len(todo), batch):
                chunk = todo[i:i + batch]
                enc = self.tok(chunk, return_tensors="pt", padding=True, truncation=True, max_length=200).to(self.dev)
                # English is rarely much longer than the Kazakh source; this also stops
                # the model from rambling on unreadable chat input.
                max_new = min(200, int(enc["input_ids"].shape[1] * 1.5) + 10)
                out = self.model.generate(**enc, forced_bos_token_id=self.tgt_id, max_new_tokens=max_new,
                                          num_beams=1, do_sample=False)
                for s, t in zip(chunk, self.tok.batch_decode(out, skip_special_tokens=True)):
                    self.cache[s] = t
                    f.write(json.dumps({"src": s, "tgt": t}, ensure_ascii=False) + "\n")
                if (i // batch) % 20 == 0:
                    print(f"  translated {i + len(chunk)}/{len(todo)}", flush=True)
        return [self.cache[t] for t in texts]


def score(rows, tr):
    res = {}
    groups = defaultdict(list)
    for r in rows:
        groups["all"].append(r)
        groups[r["profile"]].append(r)
    for cond in CONDITIONS:
        hyps = tr.translate([r[cond] for r in rows])
        for r, h in zip(rows, hyps):
            r[f"en|{cond}"] = h
    for g, rs in groups.items():
        for cond in CONDITIONS:
            res[(g, cond)] = sacrebleu.corpus_chrf([r[f"en|{cond}"] for r in rs], [[r["eng"] for r in rs]]).score
    return res


def main(names):
    tr = Translator()
    summary = {}
    for name in names:
        rows = [json.loads(l) for l in open(P / f"restored_{name}.jsonl", encoding="utf-8")]
        if name.startswith("test_flores"):
            rows = [r for r in rows if r["id"] < 300]   # first 300 sentences x 4 writer profiles
        res = score(rows, tr)
        with open(P / f"translated_{name}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\n== {name} ({len(rows)} messages) chrF ==")
        for g in sorted({gg for gg, _ in res}):
            line = "  ".join(f"{c.split()[0]} {res[(g, c)]:.1f}" for c in CONDITIONS)
            gap = res[(g, "gold")] - res[(g, "B0 raw chat")]
            rec = (res[(g, "M1 Qalaisyn")] - res[(g, "B0 raw chat")]) / gap if gap else 0
            print(f"  {g:8s} {line}  | recovered {rec:.0%}")
        summary[name] = {f"{g}|{c}": v for (g, c), v in res.items()}
    (ROOT / "results").mkdir(exist_ok=True)
    out = ROOT / "results" / "translation_chrf.json"
    old = json.loads(out.read_text()) if out.exists() else {}
    old.update(summary)
    out.write_text(json.dumps(old, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:] or ["test_tatoeba"])
