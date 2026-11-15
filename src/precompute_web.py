"""Pre-compute translations for the in-browser demo (the translator NLLB-200 is too large for a browser).
For every example we store the translation of the message as typed, Qalaisyn's restoration, the translation
after Qalaisyn, and the simple support bot's replies. Output: web/examples.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import app  # noqa: E402  (loads the model and the translator)

ROOT = Path(__file__).resolve().parents[1]
items = [m for _, m in app.SCENARIOS] + app.EXAMPLES_RU + app.EXAMPLES_LAT + [
    "ажеме жедел жардем керек уйге келиниз", "тапсырыс али келген жок акшамды кайтарыныз",
    "ертенге дарыгерге жазылуга болама", "короче ертен келем", "erekshe atap ot"]
out = {}
for msg in dict.fromkeys(items):
    m = app.clean(msg)
    fixed = app.QAL.restore(m)
    raw_en, fixed_en = app.TR.translate([m, fixed])
    out[m] = {"fixed": fixed, "raw_en": raw_en, "fixed_en": fixed_en,
              "bot_raw": app.bot_reply(raw_en), "bot_fixed": app.bot_reply(fixed_en)}
    print(m, "->", fixed, "|", raw_en, "->", fixed_en)
data = {"scenarios": [{"label": l, "msg": app.clean(m)} for l, m in app.SCENARIOS],
        "examples_ru": [app.clean(m) for m in app.EXAMPLES_RU], "examples_lat": [app.clean(m) for m in app.EXAMPLES_LAT],
        "items": out}
(ROOT / "web" / "examples.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
