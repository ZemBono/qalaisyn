"""Records a ~2 minute screen video of the Qalaisyn site being used (real browser, real clicks and typing).
Run:  .venv/Scripts/python record_demo.py   (needs the site served on http://localhost:8766)"""
import pathlib, shutil, subprocess, time
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

URL = "http://localhost:8766/"
OUT = pathlib.Path(__file__).parent / "demo_video"
OUT.mkdir(exist_ok=True)
W, H = 1280, 720

CURSOR = """
const c=document.createElement('div');
c.style.cssText='position:fixed;z-index:99999;width:18px;height:18px;border-radius:50%;background:rgba(20,20,20,.55);border:2px solid #fff;pointer-events:none;transform:translate(-50%,-50%);left:-50px;top:-50px;transition:width .12s,height .12s';
document.documentElement.appendChild(c);
addEventListener('mousemove',e=>{c.style.left=e.clientX+'px';c.style.top=e.clientY+'px'},true);
addEventListener('mousedown',()=>{c.style.width=c.style.height='12px'},true);
addEventListener('mouseup',()=>{c.style.width=c.style.height='18px'},true);
"""

SCROLL = """([y,ms])=>new Promise(r=>{const s=scrollY,d=y-s,t0=performance.now();
function f(t){const k=Math.min(1,(t-t0)/ms),e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;scrollTo(0,s+d*e);k<1?requestAnimationFrame(f):r()}
requestAnimationFrame(f)})"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        ctx = b.new_context(viewport={"width": W, "height": H}, record_video_dir=str(OUT),
                            record_video_size={"width": W, "height": H})
        pg = ctx.new_page()
        pg.goto(URL, wait_until="networkidle")
        pg.evaluate(CURSOR)
        pg.wait_for_function("document.body.innerText.includes('Engine loaded')", timeout=60000)
        mx, my = [W // 2, H // 2]

        def wait(s): time.sleep(s)

        def to(sel, ms=1600, off=70):
            y = pg.evaluate(f"document.querySelector('{sel}').getBoundingClientRect().top+scrollY-{off}")
            pg.evaluate(SCROLL, [y, ms]); wait(0.2)

        def by(dy, ms=1400):
            pg.evaluate(SCROLL, [pg.evaluate("scrollY") + dy, ms]); wait(0.2)

        def move(x, y, steps=25):
            nonlocal mx, my
            pg.mouse.move(x, y, steps=steps); mx, my = x, y

        def click(loc):
            box = loc.bounding_box()
            move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            wait(0.35); loc.click(); wait(0.3)

        # 0:00 hero: headline + the animated airline card
        move(640, 360, 1); wait(7)
        # 0:10 why one letter matters (Gulnar story)
        to("#why"); wait(6); by(330); wait(4)
        # 0:24 where it lives
        to("#where"); wait(6); by(300); wait(3)
        # 0:38 not only Kazakh
        to("#beyond"); wait(6)
        # 0:47 chatbot scenarios
        to("#bot"); wait(3)
        pills = pg.locator("#scen button")
        for i in range(min(pills.count(), 4)):
            click(pills.nth(i)); wait(4.5)
        # 1:21 type a message live
        to("#try"); wait(1.5)
        box = pg.locator("#msg")
        click(box); pg.keyboard.press("Control+A"); pg.keyboard.press("Backspace"); wait(0.6)
        pg.keyboard.type("ертен физикадан бакылау болама", delay=120); wait(4)
        ex = pg.locator("#native-ex button")
        if ex.count() > 1:
            click(ex.nth(1)); wait(4)
        # 1:40 results with the native-speaker check
        to("#results"); wait(7); by(380); wait(5)
        # 1:53 limits / closing
        pg.evaluate("[...document.querySelectorAll('h2')].find(h=>h.textContent.includes('still goes wrong')).id='limits'")
        to("#limits", 1800); wait(5)

        vid = pg.video.path()
        ctx.close(); b.close()

    mp4 = OUT / "Qalaisyn_demo.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", vid,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-r", "30", str(mp4)], check=True)
    pathlib.Path(vid).unlink()
    print(mp4)


if __name__ == "__main__":
    main()
