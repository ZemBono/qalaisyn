"""Export a compact model for the in-browser demo (web/model/*).
words.txt          one word per line (word id = line number)
stats.bin          Uint32 [uni, ctx, followers] per word id
bigrams.bin        Uint32 triples (prev_id, next_id, count), sorted by (prev_id, next_id)
meta.json          totals and settings
ru.txt             Russian words to leave alone
Word ids: 0 = <s>, 1 = </s>."""
import json
import struct
import sys
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from eval_restore import load_lexicon  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "model"
OUT.mkdir(parents=True, exist_ok=True)

MIN_WORD, MIN_BIGRAM = int(sys.argv[1]) if len(sys.argv) > 1 else 3, int(sys.argv[2]) if len(sys.argv) > 2 else 4

lex = load_lexicon()
words = ["<s>", "</s>"] + sorted(w for w, c in lex.uni.items()
                                if c >= MIN_WORD and w not in ("<s>", "</s>") and " " not in w)
wid = {w: i for i, w in enumerate(words)}
(OUT / "words.txt").write_bytes("\n".join(words).encode("utf-8"))

stats = array("I")
for w in words:
    stats.extend([min(lex.uni.get(w, 0), 2**32 - 1), lex.ctx.get(w, 0), lex.followers.get(w, 0)])
(OUT / "stats.bin").write_bytes(stats.tobytes())

big = sorted((wid[a], wid[b], c) for (a, b), c in lex.bi.items() if c >= MIN_BIGRAM and a in wid and b in wid)
bb = array("I")
for a, b, c in big:
    bb.extend([a, b, c])
(OUT / "bigrams.bin").write_bytes(bb.tobytes())

grams = [(g, c) for g, c in lex.char.counts.items() if c >= 5]
(OUT / "chars.txt").write_bytes("\n".join(f"{g}\t{c}" for g, c in grams).encode("utf-8"))

meta = {"total": lex.total, "char_order": lex.char.n, "vocab_full": len(lex.uni), "words": len(words), "bigrams": len(big),
        "min_word": MIN_WORD, "min_bigram": MIN_BIGRAM, "little_endian": sys.byteorder == "little"}
(OUT / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
(OUT / "ru.txt").write_bytes("\n".join(l.strip() for l in (ROOT / "data" / "ru_words.txt").read_text(
    encoding="utf-8").splitlines() if l.strip()).encode("utf-8"))
for p in sorted(OUT.iterdir()):
    print(f"{p.name:12s} {p.stat().st_size / 1e6:6.2f} MB")
print(meta)
