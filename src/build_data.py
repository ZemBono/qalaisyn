"""Build training corpus and held-out test sets.

Training text : Kazakh Wikipedia + Tatoeba Kazakh sentences (minus test sentences)
Test sets     : FLORES-200 devtest (kaz + professional English), Tatoeba kaz-eng pairs
Tuning set    : FLORES-200 dev
Nothing from a test set is allowed into training.
"""
import bz2
import json
import random
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).parent))
from chatify import PROFILE_NAMES, chatify, normalize_cyr  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

CYR = re.compile(r"[а-яёәғқңөұүһі]", re.I)
LAT = re.compile(r"[a-z]", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")


def good_sentence(s: str) -> bool:
    n_cyr, n_lat = len(CYR.findall(s)), len(LAT.findall(s))
    words = s.split()
    return 3 <= len(words) <= 40 and n_cyr > 10 * (n_lat + 1) / 2 and n_lat < 3


def read_lines(p):
    return [l.rstrip("\n") for l in open(p, encoding="utf-8")]


def main(max_wiki=1_500_000):
    # ---------------- test sets
    fl = RAW / "flores200_dataset"
    flores_test = list(zip(read_lines(fl / "devtest/kaz_Cyrl.devtest"), read_lines(fl / "devtest/eng_Latn.devtest")))
    flores_dev = list(zip(read_lines(fl / "dev/kaz_Cyrl.dev"), read_lines(fl / "dev/eng_Latn.dev")))

    kaz = {}
    for line in open(RAW / "kaz_sentences.tsv", encoding="utf-8"):
        sid, _, text = line.rstrip("\n").split("\t", 2)
        kaz[sid] = text
    links = [l.split() for l in read_lines(RAW / "kaz-eng_links.tsv")]
    need_eng = {e for _, e in links}
    eng = {}
    with open(RAW / "eng_sentences.tsv", encoding="utf-8") as f:
        for line in f:
            sid, _, text = line.rstrip("\n").split("\t", 2)
            if sid in need_eng:
                eng[sid] = text
    tat_pairs, seen = [], set()
    for k, e in links:
        if k in kaz and e in eng and k not in seen:
            seen.add(k)
            tat_pairs.append((kaz[k], eng[e]))
    tat_test_ids = seen

    test_norm = {normalize_cyr(k) for k, _ in flores_test + flores_dev + tat_pairs}

    # ---------------- training text
    tat_train = [normalize_cyr(t) for sid, t in kaz.items() if sid not in tat_test_ids]
    tat_train = [s for s in tat_train if s and s not in test_norm]

    wiki, wseen = [], set()
    pf = pq.ParquetFile(RAW / "kkwiki.parquet")
    for batch in pf.iter_batches(columns=["text"], batch_size=2000):
        for doc in batch.column(0).to_pylist():
            for s in SENT_SPLIT.split(doc):
                s = s.strip()
                if not good_sentence(s):
                    continue
                n = normalize_cyr(s)
                if len(n.split()) < 3 or n in wseen or n in test_norm:
                    continue
                wseen.add(n)
                wiki.append(n)
        if len(wiki) >= max_wiki:
            break
    random.Random(0).shuffle(wiki)

    (OUT / "train_wiki.txt").write_text("\n".join(wiki), encoding="utf-8")
    (OUT / "train_tatoeba.txt").write_text("\n".join(tat_train), encoding="utf-8")

    # ---------------- chat-style versions of the test sets (4 writer profiles)
    def make(pairs, name):
        rows = []
        for i, (k, e) in enumerate(pairs):
            for p in PROFILE_NAMES:
                rng = random.Random(f"{name}-{i}-{p}")
                rows.append({"id": i, "profile": p, "kaz": k, "gold": normalize_cyr(k),
                             "chat": chatify(k, p, rng), "eng": e})
        with open(OUT / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return rows

    make(flores_test, "test_flores")
    make(tat_pairs, "test_tatoeba")
    make(flores_dev, "dev_flores")
    print(f"wiki sentences: {len(wiki):,}  tatoeba train: {len(tat_train):,}")
    print(f"test: flores {len(flores_test)}, tatoeba {len(tat_pairs)}; dev flores {len(flores_dev)}")


if __name__ == "__main__":
    main()
