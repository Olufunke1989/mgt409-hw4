# Campus Customs: Usability Improvements (Problem 9)

By the time I got to Problem 9, the main features were all working: browsing,
product pages, accounts, a chatbot that checks the database, and saved
conversations. This round was about making the shop feel easier and more
trustworthy to use, so I focused on four things.

---

## 1. Making products easier to find

**What I added**

- The Products page now has a proper **filter panel** next to the results:
  - **Category:** T-Shirts, Crewnecks, Hoodies, Quarter-Zips, Jackets & Fleece,
    and Long Sleeves.
  - **Size in stock:** XS to XXL. Picking a size only shows items you can
    actually buy in that size right now, based on live inventory.
  - **Price:** Under $40, $40–$60, $60–$80, and $80 & up.
- **Everything updates on its own.** Typing in the search box refreshes the
  results after a short pause, and clicking a filter changes them right away,
  so you never have to press Search.
- The search understands normal shopper language: "hoodies", "tees",
  "1/4 zip", "Berkeley", "navy" and so on. It's the same smart matching the
  chatbot uses.
- Active filters show up as little pink tags (like *"hoodies" ✕* or
  *Size L ✕*), so you can remove one with a click, or use **Clear all**.
- The result count shows the price span too, e.g. "18 products · all $68.00".
- Filters are saved in the page address, so a filtered view can be shared or
  bookmarked. The chatbot's "See all" button uses this as well.

**Why it matters**

With 102 products, scrolling through everything gets tiring fast. Now someone
who wants "a hoodie in large under $70" can get there in three clicks. The
size filter is the part I like most, because it hides things that are sold out
in your size, so nobody falls for something they can't buy. For the business,
fewer dead ends should mean more people find something and actually buy it.

---

## 2. A smoother experience on phones and computers

**What I added**

- **Phone-friendly filters:** on smaller screens the filter panel turns into a
  slide-up sheet. You open it with a **Filters** button that shows how many are
  active, close it by tapping outside it or pressing "Show N results".
- **The chat no longer gets in the way on phones.** It opens full screen with
  a large close button, and the floating chat button steps aside while it's
  open. When the chatbot puts products on the page, a small notification pops
  up ("12 products added to the page · View"), and tapping View closes the chat
  so you can see the cards.
- On desktop, the chat button now says **"Ask us"**, so it's obvious what it is.
- **Clearer loading messages:** "Loading products…" and "Loading product
  details…" sit next to the placeholder cards, so a short wait doesn't look like
  a broken page.
- **Helpful notifications:** small pop-ups for things like "You're logged
  out. See you soon!" and "Welcome, Jordan! You're logged in."
- **Friendly problem messages:** if products can't load, you see a plain
  explanation and a **Try again** button, not a blank page.
- **A kinder "no results" screen:** instead of an empty grid, it explains that
  nothing matched, suggests other words to try, and offers **Remove filters**
  and **See all products** buttons.
- Smaller fixes: the chat results header wraps neatly on phones, "Sort by"
  stays on one line, and I checked that no page scrolls sideways at phone,
  tablet or desktop width.

**Why it matters**

A lot of students and parents will shop from their phones, often in a hurry.
If the chat covers the product they're looking at, or a search just shows
nothing, they'll probably give up. Clear messages make the site feel looked
after, which matters when you're asking someone to trust you with their order.

---

## 3. Better product recommendations from the chatbot

**What I added**

- A new chatbot tool, **`recommend_products`**, for open-ended requests like
  "I'm looking for a Yale gift under $40" or "something warm for game day in a
  large". It filters the real catalogue by:
  - **budget** (max and/or min price)
  - **type of item** (category)
  - **size**, keeping only items in stock in that size
  - **theme words** like a sport, a college, a color, or "warm"
- It only suggests products that are **in stock**, and it mixes categories, so
  you don't get six of the same T-shirt.
- The chatbot names two or three picks with their **real prices** (and sizes
  when you mention one), and the full set appears as **product cards** on the
  page with a "See all" link that opens the Products page with the same
  filters.
- If some words don't match anything (like "game day"), the tool drops just
  those words, keeps the budget and size, and the bot says what it left out. If
  nothing fits at all ("anything under $20?"), it says so honestly and
  suggests loosening one thing.

**Examples from testing** (all checked against the database)

| What the customer asked | What came back |
|---|---|
| "I'm looking for a Yale gift under $40" | T-shirts at $32, like the Tri Blend Sports Football T Shirt and the 2025 Yale Vs Harvard T Shirt |
| "Something warm for game day in a large, under $100" | Yale Sports Hoodie Tennis ($45), Champion Reverse Weave Hoodie 1 ($68), Super Heavyweight Crewneck Arched Yale Crest ($58), all in stock in L |
| "My dad loves sailing. Any ideas under $70 in XL?" | Sailing Left Chest Hoodie, $68, in stock in XL |
| "A gift for my mom, she wears a medium, budget around $70" | Yale Maplehouse Diana Mockneck, UA Gameday Double Knit Hood, Yale Sports Hoodie Tennis (all $45, all in stock in M) |
| "Do you have anything under $20?" | An honest "nothing under $20", with a suggestion to raise the budget |

**Why it matters**

A lot of shoppers don't know exactly what they want. They know who it's for
and how much they want to spend. Before, the bot could only answer questions
about items you already knew the name of. Now it can actually help someone
shop, the way a person working in the store would. Because everything comes
from the database, it never recommends something that doesn't exist or isn't
in stock.

---

## 4. A more reliable and responsive chatbot

**What I added**

- **Instant answers for simple questions.** Messages like "What hoodies do you
  have?", "Show me your quarter zips" or "How much is this?" (on a product page)
  are answered straight from the database, with no AI call. They come back in
  about **0.03 seconds instead of 3 or more**, and they're marked
  "⚡ Instant answer from our catalogue". Anything with extra details (a budget,
  a color, "for my dad") still goes to the AI.
- **One automatic retry.** If the AI service has a brief hiccup (a connection
  blip, being overloaded, or a rate limit), the backend quietly tries once more
  before giving up.
- **A time limit.** The AI gets up to 45 seconds, and the website gives up
  after 60, so the chat can't hang forever.
- **Friendly fallbacks instead of errors.** If the AI really is unavailable,
  the customer sees something like *"Sorry, our assistant is having trouble
  connecting right now…"*. If their message looked like a product search, the
  backend still finds matching products in the database and puts them on the
  page. These "sorry" replies aren't saved into the customer's history.
- **A Try again button** on any failed message. It resends the message
  without making a duplicate.
- **Faster searches:** the word lists used for product matching are built once
  and reused, instead of being rebuilt for every message.
- The backend logs how each message was answered (instant, AI, or fallback)
  and how long it took. That made the testing below possible.

**What I tested**

| Situation | Result |
|---|---|
| "Show me your quarter zips" (normal) | Instant database answer in 0.03s with 11 cards |
| "Do you have any navy hoodies?" (normal) | AI answer in about 3s with 25 matches (checked against the database) |
| AI service unreachable: "Do you have any navy hoodies?" | A friendly "trouble connecting" message, plus the 25 navy hoodies on the page, in about 4s (after one retry) |
| AI service unreachable: "What is your return policy?" | A friendly message pointing to the Products page. No technical error. |
| AI service unreachable: "What hoodies do you have?" | Still worked, because instant answers don't need the AI |
| Shop server stopped completely | The chat showed "Sorry, I had trouble answering…" with Try again. After restarting, Try again gave the right answer (Berkeley 1/4 Zip, 25 in medium, $72). |

**Why it matters**

A chatbot that sometimes shows a blank box or an error code makes the whole
store look unreliable. Now the worst case is a polite "please try again", and
often the customer still gets useful products. The instant answers also make
the common questions feel snappy and cut down on AI costs, which matters if
the shop ever gets real traffic.

---

## Everything else still works

After these changes, I re-checked the earlier features:

- product pages (stock for each size, images)
- login, wrong-password and duplicate-account handling
- saved chat history for logged-in customers, and no access for guests
- the chatbot knowing which product page you're on

All of them behaved the same as before.
