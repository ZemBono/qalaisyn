"""Cyrillic chat-style test sets (Russian keyboard / partial Kazakh keyboard) from the same held-out sentences."""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from chatify import CYR_PROFILES, chatify_cyr  # noqa: E402

P = Path(__file__).resolve().parents[1] / "data" / "processed"

for name in ["test_tatoeba", "test_flores", "dev_flores"]:
    seen, rows = set(), []
    for line in open(P / f"{name}.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        for p in CYR_PROFILES:
            rr = {k: r[k] for k in ("id", "kaz", "gold", "eng")}
            rr["profile"] = p
            rr["chat"] = chatify_cyr(r["kaz"], p, random.Random(f"{name}-{r['id']}-{p}"))
            rows.append(rr)
    with open(P / f"{name}_cyr.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(rows), "messages")
