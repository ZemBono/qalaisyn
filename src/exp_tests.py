import math, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from eval_restore import load_lexicon, load, evaluate
from restore import QalaisynRestorer, SHORT_FORM_ENDS
lex = load_lexicon()
old = QalaisynRestorer(lex, fuzzy=True, name="old")
new = QalaisynRestorer(lex, fuzzy=True, name="new", vowel_drop=True, drop_below=10**9, drop_penalty=math.log(0.05),
                       drop_chars=SHORT_FORM_ENDS, keep_names=True)
for s in ["test_tatoeba_cyr", "test_flores_cyr", "test_tatoeba", "test_flores"]:
    t, outs = evaluate([old, new], load(s))
    full = lambda n: sum(o[n] == o["gold"] for o in outs) / len(outs)
    print(f"{s:18s} old {t['old']['WER']:.2%} ({full('old'):.1%} full)   new {t['new']['WER']:.2%} ({full('new'):.1%} full)", flush=True)
