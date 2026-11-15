"""Render WRITEUP.md (+ one chart) to a one-page WRITEUP.pdf via headless Chrome."""
import base64
import subprocess
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
md = (ROOT / "WRITEUP.md").read_text(encoding="utf-8")
img = base64.b64encode((ROOT / "figures/messages.png").read_bytes()).decode()
body = markdown.markdown(md, extensions=["tables"])
body = body.replace("<h2>What we added</h2>",
                    f'<img src="data:image/png;base64,{img}" class="chart"><h2>What we added</h2>', 1)
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 10mm 12mm; }}
body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 8.45pt; line-height: 1.32; color: #1B2433; }}
h1 {{ font-size: 15.5pt; line-height: 1.15; margin: 0 0 2px; color: #1B2433; letter-spacing: -.01em; }}
h1 + p {{ color: #5F6B7A; margin-bottom: 6px; }}
h2 {{ font-size: 10pt; margin: 7px 0 2px; color: #00737D; }}
p {{ margin: 2px 0 4px; }}
strong {{ color: #1B2433; }}
em {{ color: #2B3646; }}
table {{ border-collapse: collapse; width: 100%; font-size: 8.1pt; margin: 3px 0 4px; }}
th, td {{ border-bottom: 1px solid #DCE1E7; padding: 2.5px 5px; text-align: left; }}
th {{ color: #5F6B7A; font-weight: 600; border-bottom: 1.5px solid #B9C3CE; }}
td:last-child {{ color: #00737D; }}
ol {{ margin: 2px 0 2px 16px; padding: 0; }}
img.chart {{ width: 52%; display: block; margin: 0 auto; }}
code {{ font-family: Consolas, monospace; font-size: 7.8pt; background: #F1F4F7; padding: 0 3px; border-radius: 3px; }}
</style></head><body>{body}</body></html>"""
(ROOT / "WRITEUP.html").write_text(html, encoding="utf-8")
chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
with tempfile.TemporaryDirectory() as prof:
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={prof}",
                    f"--print-to-pdf={ROOT / 'WRITEUP.pdf'}", (ROOT / "WRITEUP.html").as_uri()],
                   check=True, timeout=120)
print("WRITEUP.pdf written")
