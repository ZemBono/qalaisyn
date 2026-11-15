"""One demo video (< 3 min): a quick tour of the site, then the real extension inside Google Translate.
Real browser (Edge + the extension), real clicks and typing. Run: .venv/Scripts/python record_full.py"""
import pathlib, subprocess, time
import imageio_ffmpeg
from playwright.sync_api import sync_playwright


OUT = pathlib.Path(__file__).parent / "demo_video"
SITE = "http://localhost:8766/"
GT = "https://translate.google.com/?sl=kk&tl=en&op=translate"
SRC = 'textarea[aria-label="Source text"]'
EXAMPLES = ["ушак кашан конады", "менин жугим жогалып кетти",          # Russian keyboard
            "balamnyn kyzuy koterildi", "jeke kualigimdi jogaltyp aldym"]  # Latin letters
VIEW = (1440, 810)

CURSOR = """
const c=document.createElement('div');
c.style.cssText='position:fixed;z-index:2147483646;width:18px;height:18px;border-radius:50%;background:rgba(20,20,20,.5);border:2px solid #fff;pointer-events:none;transform:translate(-50%,-50%);left:-50px;top:-50px;transition:width .12s,height .12s';
document.documentElement.appendChild(c);
addEventListener('mousemove',e=>{c.style.left=e.clientX+'px';c.style.top=e.clientY+'px'},true);
addEventListener('mousedown',()=>{c.style.width=c.style.height='12px'},true);
addEventListener('mouseup',()=>{c.style.width=c.style.height='18px'},true);
"""
SCROLL = """([y,ms])=>new Promise(r=>{document.documentElement.style.scrollBehavior='auto';
const s=scrollY,d=y-s,t0=performance.now(),dur=Math.max(ms,Math.min(3200,1100+Math.abs(d)*0.85));
function f(t){const k=Math.min(1,(t-t0)/dur),e=-(Math.cos(Math.PI*k)-1)/2;scrollTo(0,s+d*e);k<1?requestAnimationFrame(f):r()}
requestAnimationFrame(f)})"""


def main():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            __import__("tempfile").mkdtemp(), channel="msedge", headless=False,
            args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}", "--lang=en-US"],
            viewport={"width": VIEW[0], "height": VIEW[1]}, locale="en-US",
            record_video_dir=str(OUT), record_video_size={"width": VIEW[0], "height": VIEW[1]})
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        w = lambda s: time.sleep(s)

        def cursor(): pg.evaluate(CURSOR)

        def to(sel, ms=1300, off=72):
            y = pg.evaluate(f"document.querySelector('{sel}').getBoundingClientRect().top+scrollY-{off}")
            pg.evaluate(SCROLL, [y, ms]); w(0.2)

        def by(dy, ms=1100):
            pg.evaluate(SCROLL, [pg.evaluate("scrollY") + dy, ms]); w(0.2)

        def click(loc):
            b = loc.bounding_box()
            pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=18); w(0.3); loc.click(); w(0.2)

        # ---------- part 1: the site, only the key parts ----------
        pg.goto(SITE, wait_until="networkidle"); cursor()
        pg.wait_for_function("document.body.innerText.includes('Engine loaded')", timeout=60000)
        pg.mouse.move(700, 500); w(9)                 # headline + airline example animates
        by(560); w(5)                                  # "It works inside other systems"
        to("#why"); w(7)                               # Gulnar
        to("#where"); w(6)                             # where it lives
        to("#bot"); w(1.5)
        pills = pg.locator("#scen button")
        click(pills.nth(0)); w(4.5)                    # bank
        click(pills.nth(1)); w(4.5)                    # airline
        to("#try"); w(1)
        box = pg.locator("#msg")
        click(box); pg.keyboard.press("Control+A"); pg.keyboard.press("Backspace"); w(0.4)
        pg.keyboard.type("ертен физикадан бакылау болама", delay=95); w(3.5)
        to("#results"); w(7)                           # native-speaker check
        to("#why-not-llm"); w(3); to(".llm-cmp", 900, 140); w(6)   # ChatGPT comparison
        to("#extension"); w(6)                         # the extension section

        # ---------- part 2: the extension inside Google Translate ----------
        pg.goto(GT, wait_until="domcontentloaded"); w(2.5)
        src = pg.locator(SRC)
        src.click(); w(0.6)
        for i, text in enumerate(EXAMPLES):
            if i:
                src.fill(""); w(1)
            pg.keyboard.type(text, delay=70)
            w(5)                                       # the wrong / missing translation stays visible
            pg.keyboard.press("Alt+KeyQ")
            w(5)                                       # letters restored, translation updates
        w(1.5)

        vid = pg.video.path()
        ctx.close()

    mp4 = OUT / "Qalaisyn_demo_full.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", vid, "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "21", "-r", "30", str(mp4)], check=True)
    pathlib.Path(vid).unlink()
    print(mp4)


EXT = str(pathlib.Path(__file__).parent / "extension")

if __name__ == "__main__":
    main()
