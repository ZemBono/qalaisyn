"""Render WRITEUP.md (+ main chart) to WRITEUP.pdf via headless Edge."""
import base64
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
md = (ROOT / "WRITEUP.md").read_text(encoding="utf-8")
img = base64.b64encode((ROOT / "figures/messy_messages.png").read_bytes()).decode()
body = markdown.markdown(md, extensions=["tables"])
# put the chart right after "What we built"
body = body.replace("<h2>What we added</h2>",
                    f'<img src="data:image/png;base64,{img}" style="width:40%;display:block;margin:0 auto">'
                    "<h2>What we added</h2>", 1)
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 11mm 12mm; }}
body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 8.5pt; line-height: 1.28; color: #1f2937; }}
h1 {{ font-size: 15pt; margin: 0 0 2px; color: #0b5d4b; }}
h2 {{ font-size: 10.5pt; margin: 8px 0 2px; color: #0f9d74; border-bottom: 1px solid #e5e7eb; }}
p {{ margin: 2px 0 4px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 8.3pt; margin: 3px 0; }}
th, td {{ border: 1px solid #d1d5db; padding: 2px 4px; text-align: left; }}
th {{ background: #f3f4f6; }}
ol {{ margin: 2px 0 2px 16px; padding: 0; }}
</style></head><body>{body}</body></html>"""
(ROOT / "WRITEUP.html").write_text(html, encoding="utf-8")
import tempfile

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
with tempfile.TemporaryDirectory() as prof:
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={prof}",
                    f"--print-to-pdf={ROOT / 'WRITEUP.pdf'}", (ROOT / "WRITEUP.html").as_uri()],
                   check=True, timeout=120)
print("WRITEUP.pdf written")
