"""Assemble a ready-to-upload Hugging Face Space (Gradio) in ../Qalaisyn-space."""
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT.parent / "Qalaisyn-space"
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "src").mkdir(parents=True)
(OUT / "data").mkdir()
for f in ["restore.py", "eval_restore.py", "eval_translate.py", "chatify.py", "latin.py", "app.py"]:
    shutil.copy(ROOT / "src" / f, OUT / "src" / f)
shutil.copy(ROOT / "data" / "lexicon.pkl", OUT / "data" / "lexicon.pkl")
shutil.copy(ROOT / "data" / "ru_words.txt", OUT / "data" / "ru_words.txt")
(OUT / "app.py").write_text(
    "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent / 'src'))\n"
    "from app import demo  # noqa: E402\n\ndemo.launch()\n", encoding="utf-8")
(OUT / "requirements.txt").write_text("sacrebleu\ntorch\ntransformers==4.46.3\nsentencepiece\n", encoding="utf-8")
(OUT / "README.md").write_text("""---
title: Qalaisyn
emoji: 💬
colorFrom: green
colorTo: yellow
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
license: cc-by-nc-4.0
---

# Qalaisyn

An engine that sits inside chatbots and translators and understands Kazakh the way people really type it
(Russian keyboard or Latin letters, without the special Kazakh letters). Prototype for the Veritas AI High School
Hackathon 2026, Languages track. Translator used for the comparison: NLLB-200 (Meta).
""", encoding="utf-8")
print("Space ready in", OUT, [p.name for p in OUT.iterdir()])
