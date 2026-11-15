"""Collect the headline numbers for the demo site into web/results.json (so the page always matches the notebook)."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
val = json.loads((R / "value.json").read_text(encoding="utf-8"))
conf = json.loads((R / "confidence.json").read_text(encoding="utf-8"))
chrf = json.loads((R / "translation_chrf.json").read_text())
real = json.loads((R / "real.json").read_text(encoding="utf-8")) if (R / "real.json").exists() else None
vr, vt = val["Russian keyboard, everyday"], val["Russian keyboard + 15% typos"]
out = {
    "ru_words_wrong_typed": vr["word_error_rate"]["as_typed"],
    "ru_words_wrong_dict": vr["word_error_rate"]["dictionary"],
    "ru_words_wrong_qal": vr["word_error_rate"]["qalaisyn"],
    "ru_msgs_right_dict": vr["messages_fully_right"]["dictionary"],
    "ru_msgs_right_qal": vr["messages_fully_right"]["qalaisyn"],
    "typos_msgs_right_dict": vt["messages_fully_right"]["dictionary"],
    "typos_msgs_right_qal": vt["messages_fully_right"]["qalaisyn"],
    "flagged": conf["test_tatoeba_cyr"]["at_threshold"]["flagged_share"],
    "caught": conf["test_tatoeba_cyr"]["at_threshold"]["errors_caught"],
}
if real:
    w = real["wer"]
    out.update({"real_n": real["n"], "real_typed": w["B0 raw chat"], "real_dict": w["B2 dictionary"],
                "real_before": w["M2 before native check"], "real_qal": w["M2 Qalaisyn+typos"], "real_gpt": 0.129,
                "real_chrf": real["chrf_vs_correct_translation"]})
(ROOT / "web" / "results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
for f in ["messages.png", "meaning.png"]:
    shutil.copy(ROOT / "figures" / f, ROOT / "web" / "img" / f)
shutil.copy(ROOT / "WRITEUP.pdf", ROOT / "web" / "WRITEUP.pdf")
print(json.dumps(out, indent=1))
