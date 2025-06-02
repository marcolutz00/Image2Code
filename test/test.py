import requests, random, asyncio, aiohttp, pathlib, csv
from datetime import date

# 1. Domain-Feed holen (Beispiel: 14-Tage-Liste – plain text)
url = "https://raw.githubusercontent.com/xRuffKez/NRD/main/14d/domains.txt"
domains = requests.get(url, timeout=30).text.splitlines()

# 2. Zufällig 300 Domains zum Testen auswählen
sample = random.sample(domains, 300)

# 3. Asynchron HTML + Screenshot (Playwright)
from playwright.async_api import async_playwright

# async def fetch_site(domain, outdir="data"):
#     out = pathlib.Path(outdir); out.mkdir(exist_ok=True)
#     async with async_playwright() as p:
#         browser = await p.chromium.launch()
#         page   = await browser.new_page()
#         try:
#             await page.goto(f"https://{domain}", timeout=15000)
#             html = await page.content()
#             (out / f"{domain}.html").write_text(html, encoding="utf-8")
#             await page.screenshot(path=str(out / f"{domain}.png"), full_page=True)
#         except Exception:
#             pass
#         finally:
            # await browser.close()

# asyncio.run(asyncio.gather(*(fetch_site(d) for d in sample)))
