# Comfort Menu

Any menu, in your format, at your pace.

Comfort Menu is a prototype built at Hack for Accessibility 2026. It turns a restaurant menu into the format a person chooses, shows what fits their food needs first, and hands the finished order to the crew as a clear card they can read or hear.

Live site (sample menus only): https://zona-n.github.io/comfort-menu/

## What it does

- **Four formats:** Listen (the page reads aloud), Large print, Pictures (one question at a time), and Quiet (no sound, show the order on screen).
- **My food needs:** Set allergens, diet, textures, tastes and smells to avoid, other words to avoid, and a budget once. Every menu then shows what fits first and says why other dishes do not fit.
- **What it is like:** Each dish has a plain description plus texture, taste, smell, color, and serving temperature.
- **Translation:** A menu in another language is shown in plain English, with the original name beside it. The order card goes back to the crew in the menu's language.
- **Scan a menu:** Take a photo of any menu. The server reads it with AI, translates it, and explains each dish.
- **Ask the menu:** Type "chicken under $6 with no milk" or "nothing chewy" instead of scrolling. With the server running, open questions such as "What is soft and under $15?" get a short answer.
- **Order card and crew view:** Review the order, add a note, then play it aloud or show it in very large type, with quick replies and a box for the crew to type back.
- **Captions:** Everything the page says aloud also appears as text.

## How it is built

| Part | File | What it does |
|---|---|---|
| Page | `index.html` | Everything the person sees. Works alone for the two sample restaurants. |
| Server | `backend/app.py` | A small Python (Flask) server that sends menu photos and questions to Google Gemini. |
| Key | `backend/.env` | Holds the Gemini API key. Never uploaded to GitHub. |

The server started as the team's Colab notebook: read a menu photo with Gemini, search the menu, and filter by texture. Those three steps are now `/api/scan` and `/api/ask`.

## Run it with scanning

You need Python 3.10 or newer and a Gemini API key.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Open `backend/.env` and paste the key after `GEMINI_API_KEY=`. Then:

```bash
python backend/app.py
```

Open http://localhost:8000. The Scan a menu page says "Connected to the Comfort Menu server" when it is working.

## Run it without the server

Open `index.html` in a browser, or use the live site. The two sample restaurants (Corner Grill and Chez Colette) work with no setup. Their menus were prepared in advance, so they do not show live AI.

## Keeping the key private

- The key lives only in `backend/.env` on the computer running the server, or in the hosting service's environment variables.
- `.gitignore` lists `backend/.env`, so Git never uploads it. Check with `git status`: the file must not appear.
- The key is never sent to the browser. The page only talks to the server.
- If a key is ever pasted into code, a notebook cell, a screenshot, or a commit, delete that key in Google AI Studio and make a new one.

## Safety

Comfort Menu is a guide, not medical advice. Ingredient and allergen details can be wrong or incomplete, and for scanned menus they are estimates made by AI. Anyone with an allergy or a medical diet should always confirm with restaurant staff before ordering. The sample menus are made-up restaurants with sample data.

## Accessibility

- Works with a keyboard alone, with a visible focus outline and a skip link.
- Uses real buttons, labels, and headings so screen readers can navigate it.
- Text contrast is above 4.5:1 in every format, in light and dark themes.
- Uses the Atkinson Hyperlegible typeface, designed for low-vision readers.
- No autoplay, flashing, or unexpected motion.
- A dish that does not fit is explained in words, never by color alone.

## Designed with

The food needs, texture and smell notes, budget option, and safety wording came from recommendations by members of the NeuroDivergent Social Club at the hackathon resource fair. Translation and scanning came from mentor feedback.

## Not built yet

- Photos of dishes (the page uses emoji as stand-ins).
- Finding nearby restaurants.
- Group planning for several people's needs at once.
- A public address for the server, so scanning works on the live site.
- Testing with screen-reader users and other community members.

## Team

Team AL-01, Hack for Accessibility 2026.
