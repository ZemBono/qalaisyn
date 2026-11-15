"""Experiment: expanding chat short forms (болад -> болады, жберш -> жіберші) via the dropped-final-vowel option."""
import math, sys, json
sys.path.insert(0, __import__("os").path.dirname(__file__))
from eval_restore import load_lexicon, load, evaluate
from real_eval import load_rows
from restore import QalaisynRestorer

lex = load_lexicon()
native = load_rows()
dev = load("dev_flores_cyr")
variants = {"current": dict()}
for below in (5, 50, 10**9):
    for pen in (0.05, 0.2):
        variants[f"drop below={below} p={pen}"] = dict(vowel_drop=True, drop_below=below, drop_penalty=math.log(pen))
res = {}
for name, kw in variants.items():
    m = QalaisynRestorer(lex, fuzzy=True, name=name, **kw)
    tn, _ = evaluate([m], native)
    td, _ = evaluate([m], dev)
    res[name] = (tn[name]["WER"], td[name]["WER"])
    print(f"{name:28s} native {tn[name]['WER']:.2%}   dev_flores_cyr {td[name]['WER']:.2%}", flush=True)
json.dump(res, open("results/exp_drop.json", "w"), indent=1)
