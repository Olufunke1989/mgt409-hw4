import asyncio, json
from pathlib import Path
from cdp import Browser
HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "output" / "app_check_images"  # hw4/output/app_check_images
async def main():
    b = Browser(); await b.start()
    await b.goto("http://127.0.0.1:5173/", 1)
    await b.ev("sessionStorage.setItem('cc-teaser-seen','1')")
    await b.goto("http://127.0.0.1:5173/", 3)
    await b.ev((HERE / "helpers.js").read_text())
    q = "How much is the Branford 1/4 zip, and how many do you have in size large?"
    reply = await b.ev(f"__ask({json.dumps(q)})")
    await b.shot(OUT / "01_chatbot_price_stock.png")
    print(json.dumps({"question": q, "reply": reply}, indent=1))
    await b.close()
asyncio.run(main())
