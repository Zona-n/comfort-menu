"""Comfort Menu server.

This is the team's Colab notebook turned into a small web server:

  Notebook step                              Here
  -----------------------------------------  ---------------------------------
  Read the API key from Colab Secrets        Read GEMINI_API_KEY from backend/.env
  Send a menu photo to Gemini to read it     POST /api/scan
  search_menu_with_ai(query)                 POST /api/ask
  filter_menu_by_texture(exclusion_query)    POST /api/ask (same endpoint), and
                                             texture tags on every dish in /api/scan

The AI key lives only on this server. It is never sent to the browser and
never belongs in the code or on GitHub.

Run it:   python backend/app.py      then open http://localhost:8000
"""

import base64
import binascii
import json
import os
import re
import time
from collections import defaultdict, deque
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from google import genai
from google.genai import types

BACKEND_DIR = Path(__file__).resolve().parent
SITE_DIR = BACKEND_DIR.parent

# The key is read from backend/.env (listed in .gitignore) or from the
# hosting service's environment variables.
load_dotenv(BACKEND_DIR / ".env")

# Same models the notebook used. Change them in backend/.env if needed.
SCAN_MODEL = os.environ.get("GEMINI_SCAN_MODEL", "gemini-3.8-flash")
TEXT_MODEL = os.environ.get("GEMINI_TEXT_MODEL", "gemini-3.5-flash-lite")

# Websites allowed to call this server from another address.
ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get("ALLOWED_ORIGINS", "https://zona-n.github.io").split(",")
    if origin.strip()
}

MAX_PHOTO_BYTES = 8 * 1024 * 1024
PHOTO_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
REQUESTS_PER_WINDOW = 20
WINDOW_SECONDS = 5 * 60

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

_client = None
_recent = defaultdict(deque)


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def api_key():
    return os.environ.get("GEMINI_API_KEY", "").strip()


def get_client():
    """Same as `client = genai.Client(api_key=GEMINI_API_KEY)` in the notebook."""
    global _client
    if not api_key():
        raise ApiError(503, "The server has no AI key yet. Add GEMINI_API_KEY to backend/.env and restart the server.")
    if _client is None:
        _client = genai.Client(api_key=api_key())
    return _client


def check_rate_limit():
    """Stops one visitor from using up the AI key."""
    now = time.time()
    recent = _recent[request.remote_addr or "unknown"]
    while recent and now - recent[0] > WINDOW_SECONDS:
        recent.popleft()
    if len(recent) >= REQUESTS_PER_WINDOW:
        raise ApiError(429, "Too many requests. Wait a few minutes and try again.")
    recent.append(now)


def safe_detail(error):
    """A short reason that is safe to show on the page: never contains the key."""
    detail = " ".join(str(error).split())
    if api_key():
        detail = detail.replace(api_key(), "[key hidden]")
    return detail[:220]


def ai_failed(errors):
    for line in errors:
        app.logger.error("Gemini call failed: %s", line)
    reason = errors[-1] if errors else "no reason given"
    raise ApiError(502, "The AI service could not answer. Reason: " + reason)


def ask_gemini_text(prompt):
    """Same call as the notebook: client.models.generate_content(model=..., contents=prompt)."""
    client = get_client()
    try:
        response = client.models.generate_content(model=TEXT_MODEL, contents=prompt)
        return (response.text or "").strip()
    except Exception as error:  # network problems, a wrong model name, a rejected key
        ai_failed([TEXT_MODEL + ": " + safe_detail(error)])


def ask_gemini_photo(photo, mime_type, prompt):
    """Reads a photo. Tries the notebook's way first, then two fallbacks."""
    client = get_client()
    errors = []

    # 1. The notebook's way: the Interactions API with the scan model.
    try:
        interaction = client.interactions.create(
            model=SCAN_MODEL,
            input=[
                {"type": "text", "text": prompt},
                {"type": "image", "data": base64.b64encode(photo).decode("ascii"), "mime_type": mime_type},
            ],
        )
        text = (getattr(interaction, "output_text", "") or "").strip()
        if text:
            return text
        errors.append(SCAN_MODEL + " (interactions): empty answer")
    except Exception as error:
        errors.append(SCAN_MODEL + " (interactions): " + safe_detail(error))

    # 2 and 3. The generate_content call, with the scan model and then the text model.
    for model in (SCAN_MODEL, TEXT_MODEL):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[types.Part.from_bytes(data=photo, mime_type=mime_type), prompt],
            )
            text = (response.text or "").strip()
            if text:
                return text
            errors.append(model + ": empty answer")
        except Exception as error:
            errors.append(model + ": " + safe_detail(error))

    ai_failed(errors)


def parse_json(text):
    body = re.sub(r"```json|```", "", text)
    start, end = body.find("{"), body.rfind("}")
    if start == -1 or end <= start:
        raise ApiError(502, "The menu could not be read. Try a clearer photo.")
    try:
        return json.loads(body[start:end + 1])
    except json.JSONDecodeError:
        raise ApiError(502, "The menu could not be read. Try a clearer photo.")


# The notebook asked Gemini to "Read the menu into readable, organized structure".
# This asks for the same reading as JSON, so the page can filter, sort, and speak it.
# The texture guidance comes from the notebook's filter_menu_by_texture prompt.
SCAN_PROMPT = """You read restaurant menus for people who need clear, plain information before they order.
Read the menu in this photo into a readable, organized structure. Return one JSON object only, with no markdown and no text before or after it, in exactly this shape:
{
  "restaurant": string (the restaurant name if printed, else ""),
  "language": string (English name of the language the menu is written in),
  "lang_code": string (BCP-47 code for that language, like "fr-FR"),
  "currency": string (the currency symbol used, like "$" or "€"),
  "crew": null if the menu is in English, otherwise these phrases translated into the menu language:
    {"hello": "Hello. This is my order.", "quiet": "I am ordering without speaking. Please point, write, or type your reply.", "note": "Please note", "total": "Total", "yes": "Yes", "no": "No", "write": "Please write it down", "thanks": "Thank you", "reply": "Crew: type your reply here"},
  "items": [{
    "name": plain English name of the dish,
    "original": the dish name exactly as printed,
    "category": short English category name, like "Starters" or "Drinks",
    "price": number, or null if not printed,
    "calories": calorie details exactly as printed, like "540 Cal", or "" if not printed,
    "notes": menu marks in plain words, like "gluten-free option" or "raw or undercooked", or "",
    "desc": one or two short plain English sentences: what the dish is and its main ingredients,
    "has": array of likely allergens from ["milk","egg","wheat","soy","fish","shellfish","peanut","treenut","sesame"],
    "vegetarian": true or false, "vegan": true or false, "pork": true or false,
    "feel": array from ["crunchy","chewy","mushy","jelly","spicy","sour","strongsmell","mixed"],
    "texture": short phrase, "taste": short phrase, "smell": short phrase, "color": short phrase,
    "temp": "hot", "cold", or "room",
    "pic": one emoji that looks most like the dish
  }]
}
Rules:
- List at most 30 items, in menu order.
- Use simple words a ten-year-old knows, and explain unfamiliar dish names in "desc".
- In "feel", "jelly" means jelly-like or slimy, "strongsmell" means a strong smell, and "mixed" means foods mixed together or touching.
- Texture can be subjective, so use your best judgment. For example, fries, crispy chicken, cookies, apple pies, biscuits, rice crackers, and crispy toppings are "crunchy". Soft drinks, shakes, and soft burgers are not.
- When you are unsure whether an allergen is present, include it.
- Do not invent dishes or prices that are not in the photo.
- If the photo is not a menu, return {"items": []}.
"""

# Built from the notebook's search_menu_with_ai and filter_menu_by_texture prompts.
ASK_PROMPT = """You are a helpful dining assistant and menu search assistant.
Based on the menu below, answer the customer's request: "{question}"

- If they are looking for something, find all items that match or are highly relevant. Include prices, and calorie details if the menu has them.
- If they want to avoid a texture, taste, or smell, leave out items that match or are highly likely to have it. Texture can be subjective, so use your best judgment. For example, for "no crunchy food", leave out fries, crispy chicken, cookies, apple pies, and biscuits, but keep soft items like soft drinks, shakes, or soft burgers.
- The customer's saved food needs are: {needs}. Leave out items that break them, or say clearly why an item does not fit.

Answer in plain text with no markdown: at most four short sentences, or a short list with one item per line.
Use only the menu below. If it does not say, say you do not know and suggest asking the staff.
Do not give medical advice.

Menu ({name}, prices in {currency}):
{menu}
"""


@app.errorhandler(ApiError)
def handle_api_error(error):
    return jsonify({"error": error.message}), error.status


@app.errorhandler(413)
def handle_too_large(_error):
    return jsonify({"error": "That photo is too large. Use a smaller photo."}), 413


@app.after_request
def add_cors_headers(response):
    origin = (request.headers.get("Origin") or "").rstrip("/")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "content-type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Vary"] = "Origin"
    return response


@app.get("/")
def home():
    # Only this one file is served. Nothing else in the project folder,
    # including backend/.env, can be downloaded through the server.
    return send_file(SITE_DIR / "index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "ai": bool(api_key())})


@app.route("/api/scan", methods=["POST", "OPTIONS"])
def scan():
    """Menu photo in, structured menu out."""
    if request.method == "OPTIONS":
        return "", 204
    check_rate_limit()
    data = request.get_json(silent=True) or {}
    match = re.match(r"^data:(image/[a-z]+);base64,(.+)$", str(data.get("image", "")), re.DOTALL)
    if not match or match.group(1) not in PHOTO_TYPES:
        raise ApiError(400, "Send a JPEG, PNG, GIF, or WebP photo.")
    try:
        photo = base64.b64decode(match.group(2), validate=True)
    except (binascii.Error, ValueError):
        raise ApiError(400, "That photo could not be opened. Choose another photo.")
    if len(photo) > MAX_PHOTO_BYTES:
        raise ApiError(413, "That photo is too large. Use a smaller photo.")

    text = ask_gemini_photo(photo, match.group(1), SCAN_PROMPT)
    menu = parse_json(text)
    if not isinstance(menu.get("items"), list):
        menu["items"] = []
    return jsonify({"menu": menu})


@app.route("/api/ask", methods=["POST", "OPTIONS"])
def ask():
    """A question about one menu in, a short plain answer out."""
    if request.method == "OPTIONS":
        return "", 204
    check_rate_limit()
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()[:300]
    menu = data.get("menu") if isinstance(data.get("menu"), dict) else {}
    items = menu.get("items") if isinstance(menu.get("items"), list) else []
    if not question:
        raise ApiError(400, "Type a question first.")
    if not items:
        raise ApiError(400, "Open a menu first.")

    prompt = ASK_PROMPT.format(
        question=question.replace('"', "'"),
        needs=json.dumps(data.get("needs") or {}, ensure_ascii=False)[:1000],
        name=str(menu.get("name", "menu"))[:100],
        currency=str(menu.get("currency", "$"))[:4],
        menu=json.dumps(items[:60], ensure_ascii=False)[:40000],
    )
    answer = ask_gemini_text(prompt)
    return jsonify({"answer": answer[:900] or "No answer came back. Try asking in another way."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Comfort Menu is running. Open http://localhost:{port}")
    if not api_key():
        print("No AI key found. Add GEMINI_API_KEY to backend/.env to turn on menu scanning.")
    app.run(host="127.0.0.1", port=port)
