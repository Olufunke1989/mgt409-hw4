import asyncio, json
from pathlib import Path
from cdp import Browser
HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "output" / "app_check_images"  # hw4/output/app_check_images
async def main():
    b = Browser(); await b.start()
    await b.goto("http://127.0.0.1:5173/", 1)
    await b.ev("sessionStorage.setItem('cc-teaser-seen','1')")
    await b.goto("http://127.0.0.1:5173/products", 3)
    await b.ev((HERE / "helpers.js").read_text())
    q = "What hoodies do you have?"
    reply = await b.ev(f"__ask({json.dumps(q)})")
    await asyncio.sleep(1.5)
    cards = await b.ev("""(() => { const s=document.querySelector('.chat-results'); return { title: s.querySelector('h2').innerText, count: s.querySelector('.result-count').innerText,
      cards: [...s.querySelectorAll('.product-card')].map(c => ({ name: c.querySelector('h3').innerText, price: c.querySelector('.price').innerText,
      href: c.getAttribute('href'), img: c.querySelector('img').getAttribute('src'), imgLoaded: c.querySelector('img').naturalWidth > 0,
      desc: c.querySelector('.product-card-desc').innerText.slice(0,60), x: Math.round(c.getBoundingClientRect().left) })) } })()""")
    await b.shot(OUT / "02_chat_search_cards.png")
    # Click the first card that isn't hidden behind the chat window.
    target = next(c for c in cards["cards"] if c["x"] < 700)
    await b.ev(f"""(async () => {{ document.querySelector('.chat-results a[href="{target['href']}"]').click(); await __w(2500); return true }})()""")
    detail = await b.ev("""(() => ({ path: location.pathname, h1: document.querySelector('.detail-info h1')?.innerText,
      price: document.querySelector('.price-lg')?.innerText, img: document.querySelector('.detail-image img')?.getAttribute('src'),
      imgLoaded: document.querySelector('.detail-image img')?.naturalWidth > 0,
      stock: [...document.querySelectorAll('.stock-table tbody tr')].map(r => r.innerText.replace(/\\s+/g,' ')) }))()""")
    await b.ev("document.querySelector('.chat-launcher.is-open')?.click(); window.scrollTo(0,0); true")
    await asyncio.sleep(1.2)
    await b.shot(OUT / "02b_card_opens_detail_page.png")
    print(json.dumps({"question": q, "reply": reply, "results": cards, "clicked": target, "detail": detail}, indent=1))
    await b.close()
asyncio.run(main())
