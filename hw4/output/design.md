# Campus Customs: Design Refresh (Problem 10)

By Problem 9 the shop worked well, but it still looked like a dark class
project. For Problem 10 I gave the whole site a new look without touching what
already worked. I wanted it to feel like a real lifestyle brand, the kind of
shop you'd scroll through just because it's fun to look at.

I called the look **"The New Haven Lookbook"**: a modern editorial style mixed
with something a bit more playful and artistic.

---

## Colors

I kept **Yale blue** at the heart of it (the logo mark and the biggest category
tile), but built a fuller palette around it:

- **Electric blue** for buttons, links and highlights
- **Soft lavender**, **butter yellow**, **coral** and a little **mint** for
  backgrounds, shapes and accents
- A warm **cream** background with a very faint dotted texture, instead of
  plain white or black
- A deep **navy ink** for text, the footer and the bold "Game day" band

The pastels sit behind the products and the brighter colors are saved for
things you click, so the page feels colorful without being loud or childish.
Every product card gets one of five soft background tints, so the grid feels
varied but still calm.

**Why I think it helps:** a warm, colorful site feels welcoming and premium, and
that makes people want to keep scrolling. Using color mainly for buttons and
highlights also tells shoppers where to look and what to click.

## Typography

- **Fraunces**, an elegant serif with a beautiful italic, for headlines. I mix
  regular and italic words ("Wear the *spirit* of Old Blue") to give them
  personality.
- **Plus Jakarta Sans**, a clean modern sans-serif, for everything else, so
  prices, sizes and buttons stay easy to read.

**Why it helps:** the serif makes it feel like a fashion magazine or boutique,
and the sans-serif keeps the shopping parts practical.

## The homepage

- **Hero "lookbook" collage.** Instead of a stock photo, the hero is a collage
  of three real products from my catalogue (the Big Yale hoodie, the 2025
  Harvard–Yale tee and the Benjamin Franklin 1/4 zip). They're layered and
  slightly tilted over a lavender circle and a butter-yellow arch, with a coral
  "Tees from $32" sticker. That price comes from the database. There's a big
  headline, a short welcome, and a bold **Shop Now** button.
- **A tilted blue ribbon** that slowly scrolls words like "Hoodies", "Game day
  tees" and "Residential colleges".
- **Featured picks:** four real products.
- **Shop by category:** a colorful mosaic of tiles (Yale blue, butter, lavender,
  coral, mint and electric blue). Each tile shows a real product photo and how
  many styles are in that category.
- **"Bundle up for The Game":** a dark editorial band with floating shapes.
- **Fresh picks:** one standout from each part of the shop, all in stock.
- **Visit us:** a coral card with our Broadway address.

I chose not to use outside "lifestyle" photos, because I didn't want any
picture to suggest a product we don't sell. Everything shown as merchandise is
a real item from the catalogue. I also called the last product section "Fresh
picks" instead of "New arrivals", because my database doesn't record when items
arrived, and I didn't want to label something as new if I can't back that up.

**Why it helps:** the first screen now grabs attention and shows real products
right away. Each section leads naturally to another place to explore, whether
that's a category, a product or the game-day collection.

## Products and product pages

- **Boutique-style cards:** each product sits on a soft pastel tile with a
  circle behind it, like a styled photo shoot. The name, category and a price
  "pill" sit underneath.
- **Hover effects:** on a computer, the card lifts, the photo tilts slightly
  and zooms in, the circle grows, and a little "View details →" tag slides up.
- **Products page:** a colorful banner at the top, a clean white filter panel,
  and the cards fade in gently as you scroll.
- **Product page:**
  - a large photo framed on a colored stage with shapes behind it
  - an elegant serif title and price
  - **color swatches** next to each color name
  - chunky size buttons
  - a stock list with small **stock bars**, so you can see at a glance what's
    plentiful and what's running low
  - three small reassurance notes: officially licensed, try it on at 57
    Broadway, and ask our assistant

**Why it helps:** big, clean photos and clear prices build trust. The hover
effects make browsing feel lively. The stock bars and "Only 2 left" notes make
it easy to decide, and give people a gentle reason not to wait.

## Motion and artistic details

- Sections and cards **fade up softly** as they scroll into view.
- The hero text and collage **rise in** when the page loads.
- **Buttons** lift slightly on hover, and the main buttons have a light shine
  sweep.
- **Floating shapes** drift slowly, the star in the hero turns slowly, and
  a couple of shapes move at a slightly different speed when you scroll.
- The announcement bar and the blue ribbon **scroll gently** in a loop.

I kept every animation slow and subtle. Anyone whose device is set to "reduce
motion" gets the same site with the animations turned off.

**Why it helps:** small movements make the site feel alive and polished, like
someone cared about the details, without distracting from the products.

## The chatbot

- The floating button is now a **gradient pill** (electric blue → violet →
  coral) with a chat icon, a little green "online" dot, and the words
  **"Ask us"**.
- A few seconds after you arrive, a small **welcome bubble** appears once:
  *"Hi there! 👋 Looking for a gift or the right size? I'm happy to help."*
  It greets you by first name if you're logged in.
- The chat window is titled **"Your personal shopper"**, with:
  - a colorful header, an avatar badge, and rounded corners
  - white message bubbles for the assistant and navy ones for the customer
  - colorful typing dots
- New chats show **suggestion chips**, "Gift ideas under $40", "What hoodies do
  you have?" and "Something warm in a large", so people know what to ask.
- On phones it still opens full screen with a big close button.

Everything underneath still works: product search cards, recommendations,
instant answers, saved conversations and the Try again button.

**Why it helps:** a friendly, good-looking assistant gets more people to
actually use it. The suggestion chips remove the "what do I even type?"
moment, and each one leads straight to real products.

## Navigation, footer and account pages

- **Navigation:**
  - a slim scrolling announcement bar that only shows true facts (officially
    licensed, our address, sizes XS–XXL)
  - a logo mark in Yale blue with a coral offset shadow, plus the store name in
    the serif font
  - Home, Products and About Us in a rounded pill, with the current page
    highlighted
  - clear Log In and Create Account buttons
- **Footer:**
  - a dark navy section with rounded corners and floating shapes
  - a big "Made for the ones who *bleed blue.*" call to action
  - organized Shop, Visit and Account links
  - a huge faded "Campus Customs" wordmark
- **Log in / Create account:** these now use a split design. On one side is an
  electric-blue art panel ("Your shop, *remembered.*") with real product photos;
  on the other is the form. The account pages now feel like part of the brand.
- **About Us:** a two-photo collage, numbered value cards in soft colors, and a
  closing call to action.

## Phones

I checked every page at phone, tablet and desktop sizes:

- nothing scrolls sideways
- the menu becomes a clean dropdown
- filters open as a bottom sheet
- product cards show two across
- the category mosaic becomes a neat two-column layout
- the chat fills the screen when it's open

## Fixes I made while reviewing

- The tilted blue ribbon was poking out past the screen edges and causing
  sideways scrolling, so I clipped it.
- The sticky navbar stopped sticking because of a page-level overflow rule, so
  I replaced that rule with one that doesn't break sticky headers.
- The four-item rows on the homepage left one card alone on its own line on
  medium screens. They now show 4 across, or 2×2.
- The category mosaic had a gap, and one photo covered its title. Both are
  fixed, along with the layout on phones.
- The chat window could overlap the navbar on shorter screens, so it now stays
  below it.
- A decorative circle on the sign-up panel was clipping the headline, so I
  moved it.

## Why I think this will help the business

People judge an online store in the first few seconds. The new design looks
like a real brand, so it earns trust right away. Then it gives people lots of
reasons to keep exploring:

- colorful categories
- featured and fresh picks
- a friendly assistant with ready-made questions
- product pages that make choosing a size easy

More time browsing, more confidence in what they're buying, and fewer dead ends
should all add up to more people finding something they love, and actually
buying it.
