"""Checks the extension inside Google Translate: English translation before and after Alt+Q."""
import sys, time
from playwright.sync_api import sync_playwright
from extension_test import launch

GT = "https://translate.google.com/?sl=kk&tl=en&op=translate"
SRC = 'textarea[aria-label="Source text"], textarea'


def translation(pg, prev=None, wait=12):
    t0 = time.time()
    last = ""
    while time.time() - t0 < wait:
        last = pg.evaluate("""() => { const e = document.querySelector('[jsname="W297wb"]') ||
            document.querySelector('span[lang="en"]'); return e ? e.innerText.trim() : ""; }""")
        if last and last != prev:
            time.sleep(1.2)
            return pg.evaluate("""() => [...document.querySelectorAll('[jsname="W297wb"]')].map(e=>e.innerText).join(' ').trim()
                || (document.querySelector('span[lang="en"]')||{}).innerText || ''""")
        time.sleep(0.3)
    return last


def check(pg, text):
    pg.fill(SRC, "")
    time.sleep(0.8)
    pg.click(SRC)
    pg.fill(SRC, text)
    before = translation(pg)
    pg.keyboard.press("Alt+KeyQ")
    for _ in range(80):
        fixed = pg.input_value(SRC)
        if fixed != text:
            break
        time.sleep(0.1)
    after = translation(pg, prev=before)
    return fixed, before, after


def main(cases):
    with sync_playwright() as p:
        ctx = launch(p)
        pg = ctx.new_page()
        pg.goto(GT, wait_until="domcontentloaded")
        time.sleep(3)
        for b in ("Reject all", "Отклонить все"):
            if pg.locator(f"button:has-text('{b}')").count():
                pg.locator(f"button:has-text('{b}')").first.click(); time.sleep(2)
        print("URL:", pg.url)
        for c in cases:
            fixed, before, after = check(pg, c)
            print(f"\nTYPED : {c}\nFIXED : {fixed}\nEN raw: {before}\nEN fix: {after}")
        ctx.close()


if __name__ == "__main__":
    main(sys.argv[1:] or ["ушак кешигип жатыр ма", "баламнын кызуы 39 котерилди не истеу керек",
                          "несие бойынша толемди кешиктирсем бола ма", "аударым откен жок акшам кайда",
                          "жеке куалигимди жогалтып алдым не истеу керек", "тапсырыс али келген жок акшамды кайтарыныз",
                          "ертенге даригерге жазылуга бола ма", "такси кашан келеди мен кутип турмын"])
