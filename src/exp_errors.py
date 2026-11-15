import math, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from eval_restore import load_lexicon
from real_eval import load_rows
from restore import QalaisynRestorer
lex = load_lexicon()
m = QalaisynRestorer(lex, fuzzy=True, vowel_drop=True, drop_below=50, drop_penalty=math.log(0.05))
for r in load_rows():
    h = m.restore(r["chat"])
    g = r["gold"].split(); hs = h.split()
    if h != r["gold"]:
        d = [(a, b) for a, b in zip(g, hs) if a != b] if len(g) == len(hs) else [(r["gold"], h)]
        print(r["chat"], "|", d)
