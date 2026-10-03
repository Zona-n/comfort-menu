# Comfort Menu

Any menu, in your format, at your pace.

Comfort Menu is a prototype built at Hack for Accessibility 2026. It turns a restaurant menu into the format a person chooses, shows what fits their food needs first, and hands the finished order to the crew as a clear card they can read or hear.

Live site: https://zona-n.github.io/comfort-menu/

## What it does

- **Four formats:** Listen (the page reads aloud), Large print, Pictures (one question at a time), and Quiet (no sound, show the order on screen).
- **My food needs:** Set allergens, diet, textures, tastes and smells to avoid, other words to avoid, and a budget once. Every menu then shows what fits first and says why other dishes do not fit.
- **What it is like:** Each dish has a plain description plus texture, taste, smell, color, and serving temperature.
- **Translation:** A menu in another language is shown in plain English, with the original name beside it. The order card goes back to the crew in the menu's language.
- **Scan a menu:** Take a photo of any menu. With an AI key, the page reads it, translates it, and explains each dish.
- **Ask the menu:** Type "chicken under $6 with no milk" or "nothing chewy" instead of scrolling. With an AI key, open questions such as "What is in the coq au vin?" get a short answer.
- **Order card and crew view:** Review the order, add a note, then play it aloud or show it in very large type, with quick replies and a box for the crew to type back.
- **Captions:** Everything the page says aloud also appears as text.

## Run it

Open `index.html` in a browser. There is nothing to install and no server.

The two sample restaurants (Corner Grill and Chez Colette) work with no setup. Their menus were prepared in advance, so they do not show live AI.

### Scanning a real menu

Scanning and open questions call the Anthropic API from the browser, so they need an API key:

1. Open **Choose a menu**, then **Scan a menu**, then **AI key settings**.
2. Paste an Anthropic API key and select **Save key**.
3. Choose a photo of a menu.

The key is saved only in that browser and is sent only to Anthropic. Never put a key in the code or commit one to this repository. Use a key with a low spending limit, and remove it from shared laptops after a demo.

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
- Testing with screen-reader users and other community members.

## Team

Team AL-01, Hack for Accessibility 2026.
