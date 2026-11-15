import math, sys, json
sys.path.insert(0, __import__("os").path.dirname(__file__))
from eval_restore import load_lexicon, load, evaluate
from real_eval import load_rows
from restore import QalaisynRestorer, SHORT_FORM_ENDS
lex = load_lexicon()
native = load_rows(); dev = load("dev_flores_cyr")
V = {"current": dict(),
     "short forms": dict(vowel_drop=True, drop_below=10**9, drop_penalty=math.log(0.05), drop_chars=SHORT_FORM_ENDS),
     "short forms p.2": dict(vowel_drop=True, drop_below=10**9, drop_penalty=math.log(0.2), drop_chars=SHORT_FORM_ENDS),
     "short forms + names": dict(vowel_drop=True, drop_below=10**9, drop_penalty=math.log(0.05), drop_chars=SHORT_FORM_ENDS, keep_names=True),
     "short forms p.2 + names": dict(vowel_drop=True, drop_below=10**9, drop_penalty=math.log(0.2), drop_chars=SHORT_FORM_ENDS, keep_names=True)}
for name, kw in V.items():
    m = QalaisynRestorer(lex, fuzzy=True, name=name, **kw)
    tn, outn = evaluate([m], native); td, _ = evaluate([m], dev)
    full = sum(o[name] == o["gold"] for o in outn) / len(outn)
    print(f"{name:26s} native {tn[name]['WER']:.2%} full {full:.0%}  dev {td[name]['WER']:.2%}", flush=True)
    if name == "short forms p.2 + names" or name == "short forms + names":
        for o in outn:
            if o[name] != o["gold"]:
                g, h = o["gold"].split(), o[name].split()
                print("   ", [(a, b) for a, b in zip(g, h) if a != b] if len(g) == len(h) else (o["gold"], o[name]))
