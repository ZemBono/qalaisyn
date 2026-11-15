"""Pre-compute translations for the in-browser demo (the translator NLLB-200 is too large for a browser).
For every example: translation of the message as typed, Qalaisyn's restoration, translation after Qalaisyn,
and the simple support bot's replies. Output: web/examples.json. Examples were written to show the idea and
are not used anywhere in the evaluation."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import app  # noqa: E402  (loads the model and the translator)

ROOT = Path(__file__).resolve().parents[1]

CATEGORIES = {
    "Bank": ["несие бойынша толемди кешиктирсем бола ма", "кредит толей алмай журмин комектесиниздер",
             "картамды урлап кетти бугаттаныз", "картадан акша шешилип кетипти мен ешнарсе алмадым",
             "аударым откен жок акшам кайда"],
    "Airline": ["ушак кешигип жатыр ма", "рейс кашан ушады"],
    "Clinic": ["баламнын кызуы 39 котерилди не истеу керек", "ажеме жедел жардем керек уйге келиниз",
               "ертенге дарыгерге жазылуга болама"],
    "E-government": ["жеке куалигимди жогалтып алдым не истеу керек", "тугу туралы куалик кайдан алуга болады"],
    "Shop & delivery": ["тапсырыс али келген жок акшамды кайтарыныз", "доставка канша турады",
                        "тауар сынык келди кайтарып беремин"],
    "Taxi & transport": ["такси кашан келеди мен кутип турмын", "автобус аялдамасы кай жерде"],
    "School": ["ертен сабак нешеде басталады", "уй тапсырманы жиберши"],
    "Everyday": ["салем калайсын ертен мектепке барасын ба", "уйге келе жатм кешке хабарласамын",
                 "рахмет бауырым комектескенин ушин", "короче ертен келем"],
    "Latin letters": ["balamnyn qyzuy 39 koterildi ne isteu kerek", "salem qalaisyn erteng mektepke barasyn ba",
                      "kartamdy urlap ketti bugattanyz"],
}
LIMITS = ["жуким жогалып кетти", "егов аркылы аныктаманы калай алам"]   # honest failures shown on the page
SCENARIOS = app.SCENARIOS + [("Shop: refund for a missing order", "тапсырыс али келген жок акшамды кайтарыныз")]

out = {}
msgs = [app.clean(m) for ms in CATEGORIES.values() for m in ms] + [app.clean(m) for _, m in SCENARIOS] + LIMITS
for m in dict.fromkeys(msgs):
    fixed = app.QAL.restore(m)
    raw_en, fixed_en = app.TR.translate([m, fixed])
    out[m] = {"fixed": fixed, "raw_en": raw_en, "fixed_en": fixed_en,
              "bot_raw": app.bot_reply(raw_en), "bot_fixed": app.bot_reply(fixed_en)}
    print(f"{m}\n   -> {fixed}\n   before: {raw_en}\n   after:  {fixed_en}")
data = {"scenarios": [{"label": l, "msg": app.clean(m)} for l, m in SCENARIOS],
        "categories": {c: [app.clean(m) for m in ms] for c, ms in CATEGORIES.items()},
        "limits": LIMITS,
        "items": out}
(ROOT / "web" / "examples.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
