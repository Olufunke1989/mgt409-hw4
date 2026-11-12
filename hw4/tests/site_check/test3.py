import asyncio, json
from pathlib import Path
from cdp import Browser
HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "output" / "app_check_images"  # hw4/output/app_check_images
STATE = """(() => ({ url: location.search, count: document.querySelector('.result-count')?.innerText,
  chips: [...document.querySelectorAll('.active-filters .chip')].map(c => c.innerText.replace(' ✕','')),
  products: [...document.querySelectorAll('.shop-results .product-card')].map(c => c.querySelector('h3').innerText + ' ' + c.querySelector('.price').innerText) }))()"""
async def main():
    b = Browser(); await b.start()
    await b.goto("http://127.0.0.1:5173/", 1)
    await b.ev("sessionStorage.setItem('cc-teaser-seen','1')")
    await b.goto("http://127.0.0.1:5173/products", 3)
    await b.ev((HERE / "helpers.js").read_text())
    steps = {"start": await b.ev(STATE)}
    # 1) type a keyword (results update by themselves)
    await b.ev("""(async () => { const el = document.getElementById('search'); el.focus();
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,'hoodie');
      el.dispatchEvent(new Event('input',{bubbles:true})); await __w(1800); return true })()""")
    steps["after_keyword"] = await b.ev(STATE)
    # 2) pick size L
    await b.ev("""(async () => { [...document.querySelectorAll('.size-filter .size')].find(x => x.innerText==='L').click(); await __w(1500); return true })()""")
    steps["after_size_L"] = await b.ev(STATE)
    # 3) pick price $60 – $80
    await b.ev("""(async () => { [...document.querySelectorAll('.price-option')].find(l => l.innerText.trim().startsWith('$60')).querySelector('input').click(); await __w(2000); window.scrollTo(0, 230); await __w(1200); return true })()""")
    steps["after_price"] = await b.ev(STATE)
    await b.shot(OUT / "03_search_and_filters.png")
    print(json.dumps(steps, indent=1))
    await b.close()
asyncio.run(main())
