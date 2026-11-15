"""Records the real Qalaisyn browser extension working inside Google Translate and Kazakh Wikipedia.
Run: .venv/Scripts/python record_extension.py   (uses Microsoft Edge with the extension from ./extension)"""
import pathlib, subprocess, time
import imageio_ffmpeg
from playwright.sync_api import sync_playwright
from extension_test import launch

OUT = pathlib.Path(__file__).parent / "demo_video"
GT = "https://translate.google.com/?sl=kk&tl=en&op=translate"
SRC = 'textarea[aria-label="Source text"]'
SITE = "https://zembono.github.io/qalaisyn/web/#extension"
EXAMPLES = ["менин жугим жогалып кетти", "ушак кашан конады",
            "жеке куалигимди жогалтып алдым не истеу керек", "аударым откен жок акшам кайда"]

CURSOR = """
const c=document.createElement('div');
c.style.cssText='position:fixed;z-index:2147483646;width:18px;height:18px;border-radius:50%;background:rgba(20,20,20,.55);border:2px solid #fff;pointer-events:none;transform:translate(-50%,-50%);left:-50px;top:-50px';
document.documentElement.appendChild(c);
addEventListener('mousemove',e=>{c.style.left=e.clientX+'px';c.style.top=e.clientY+'px'},true);
"""


def main():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        ctx = launch(p, video_dir=str(OUT))
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        w = lambda s: time.sleep(s)

        def show_cursor(): pg.evaluate(CURSOR)

        def click(loc):
            b = loc.bounding_box()
            pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=20); w(0.3); loc.click()

        # 1. the extension is installed in the browser
        pg.goto("edge://extensions"); w(5)

        # 2. Google Translate, Kazakh -> English
        pg.goto(GT, wait_until="domcontentloaded"); w(3); show_cursor()
        box = pg.locator(SRC)
        click(box); w(1)
        for i, text in enumerate(EXAMPLES):
            if i:
                box.fill(""); w(1.5)
            pg.keyboard.type(text, delay=85)
            w(4.5)                      # the wrong English translation stays on screen
            pg.keyboard.press("Alt+KeyQ")
            w(6.5)                      # letters restored, translation updates

        # 3. Kazakh Wikipedia search box: another site, same extension
        pg.goto("https://kk.wikipedia.org/", wait_until="domcontentloaded"); w(2); show_cursor()
        s = pg.locator("input[name=search]").first
        click(s); w(0.6)
        pg.keyboard.type("казакстан тарихы", delay=90); w(2.5)
        pg.keyboard.press("Alt+KeyQ"); w(4.5)
        pg.keyboard.press("Enter"); w(5)

        # 4. where to get it
        pg.goto(SITE, wait_until="networkidle"); w(7)

        vid = pg.video.path()
        ctx.close()

    mp4 = OUT / "Qalaisyn_extension_demo.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", vid, "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "20", "-r", "30", str(mp4)], check=True)
    pathlib.Path(vid).unlink()
    print(mp4)


if __name__ == "__main__":
    main()
