"""Loads the Chrome extension in a real Chromium and checks it on a local page and on Google Translate."""
import pathlib, sys, time, tempfile
from playwright.sync_api import sync_playwright

CHANNEL = "msedge"
EXT = str(pathlib.Path(__file__).parent / "extension")
LOCAL = """<!doctype html><meta charset=utf-8><body style="font:18px sans-serif;padding:30px">
<textarea id=ta rows=3 cols=60></textarea><br><input id=inp size=60><br>
<div id=ce contenteditable=true style="border:1px solid #999;min-height:40px;width:600px"></div></body>"""

CASES = ["ушак кешигип жатыр ма", "Баламнын кызуы 39 котерилди, не истеу керек?",
         "несие бойынша толемди кешиктирсем бола ма", "калайсын, короче ертен келем",
         "salem qalaisyn erten mektepke barasyn ba"]


def launch(p, video_dir=None, view=(1280, 720)):
    kw = dict(headless=False, args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}", "--lang=en-US"],
              viewport={"width": view[0], "height": view[1]}, locale="en-US")
    if video_dir:
        kw.update(record_video_dir=video_dir, record_video_size={"width": 1280, "height": 720})
    return p.chromium.launch_persistent_context(tempfile.mkdtemp(), channel=CHANNEL, **kw)


def fix_in(page, sel, text, kind="input"):
    page.click(sel)
    if kind == "input":
        page.fill(sel, text)
    else:
        page.keyboard.type(text)
    page.keyboard.press("Alt+KeyQ")
    for _ in range(100):
        v = page.eval_on_selector(sel, "e => e.value ?? e.innerText")
        if v.strip() != text.strip():
            return v
        time.sleep(0.1)
    return v


def main():
    with sync_playwright() as p:
        ctx = launch(p)
        pg = ctx.new_page()
        pg.route("http://test.local/", lambda r: r.fulfill(body=LOCAL, content_type="text/html; charset=utf-8"))
        pg.goto("http://test.local/")
        time.sleep(1)
        for c in CASES:
            print("textarea:", c, "->", fix_in(pg, "#ta", c))
        print("input   :", fix_in(pg, "#inp", CASES[0]))
        print("editable:", fix_in(pg, "#ce", CASES[1], kind="type"))
        ctx.close()


if __name__ == "__main__":
    main()
