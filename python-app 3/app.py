from __future__ import annotations
import json
import os
from typing import Generator

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from config import Config
from openai import OpenAI

app = Flask(__name__)
app.config.from_object(Config)

client = OpenAI(api_key=app.config["OPENAI_API_KEY"]) if app.config["OPENAI_API_KEY"] else None

ALLOWED_MODELS = {
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
}

SYSTEM_PROMPT = '''You are Meal Plan Specialist, a culinary assistant that crafts practical, culturally aware meal plans that a best for health. 
    You Always consider dietary preferences, allergies, and local ingredients.
    Provide realistic prep times and concise instructions.
    Offer substitutions and leftover tips to reduce waste.
    Keep tone friendly and professional.
    Return the plain text. Dont use markdowns.
    '''


@app.after_request
def set_security_headers(resp):
    csp = app.config.get("CONTENT_SECURITY_POLICY")
    if csp:
        resp.headers["Content-Security-Policy"] = csp
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp

@app.route("/")
def index():
    if not app.config["OPENAI_API_KEY"]:
        warn = "Missing OPENAI_API_KEY. Set it in your .env."
    else:
        warn = None
    return render_template("index.html", warn=warn, model=app.config["OPENAI_MODEL"])

# Chat (basic JSON)
@app.post("/api/chat")
def api_chat():
    if client is None:
        return jsonify({"error": "Server missing OPENAI_API_KEY"}), 500

    payload = request.get_json(force=True)
    messages = payload.get("messages", [])
    model = payload.get("model", app.config["OPENAI_MODEL"])
    if model not in ALLOWED_MODELS:
        model = app.config["OPENAI_MODEL"]

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=app.config["TEMPERATURE"],
            max_tokens=app.config["MAX_TOKENS"],
            messages=messages,
        )
        content = resp.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Chat (SSE streaming)
@app.post("/api/chat/stream")
def api_chat_stream():
    if client is None:
        return jsonify({"error": "Server missing OPENAI_API_KEY"}), 500

    payload = request.get_json(force=True)
    messages = payload.get("messages", [])
    model = payload.get("model", app.config["OPENAI_MODEL"])
    if model not in ALLOWED_MODELS:
        model = app.config["OPENAI_MODEL"]

    def generate() -> Generator[str, None, None]:
        try:
            for chunk in client.chat.completions.create(
                model=model,
                temperature=app.config["TEMPERATURE"],
                max_tokens=app.config["MAX_TOKENS"],
                messages=messages,
                stream=True,
            ):
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield f"data: {json.dumps({'delta': delta})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # disable buffering on some proxies
    }
    return Response(stream_with_context(generate()), headers=headers)

# Meal Plan (structured JSON)
# @app.post("/api/mealplan")
# def api_mealplan():
    if client is None:
        return jsonify({"error": "Server missing OPENAI_API_KEY"}), 500

    data = request.get_json(force=True)
    prefs = {
        "days": int(data.get("days", 7)),
        "meals_per_day": int(data.get("meals_per_day", 3)),
        "calories": int(data.get("calories", 2100)),
        "diet": data.get("diet", "balanced"),
        "cuisine": data.get("cuisine", "any"),
        "exclusions": data.get("exclusions", []),
        "budget": data.get("budget", "moderate"),
        "locale": data.get("locale", "en-US"),
    }

    USER_INSTRUCTIONS = (
        "Create a {days}-day meal plan with {meals_per_day} meals per day. Target ~{calories} kcal/day.\n"
        "Dietary style: {diet}. Preferred cuisine: {cuisine}. Exclusions/allergies: {exclusions}.\n"
        "Budget: {budget}. Return STRICT JSON only with this schema: \n"
        "{"
        "  'days': [ { 'label': 'Day 1', 'totals': { 'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0 }, "
        "    'meals': [ { 'name': '', 'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0, 'prep_time_min': 0, 'ingredients': [], 'instructions': '' } ] } ],"
        "  'shopping_list': [ 'item' ],"
        "  'notes': 'short tips'"
        "}"
    ).format(**prefs)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_INSTRUCTIONS},
    ]

    try:
        resp = client.chat.completions.create(
            model=app.config["OPENAI_MODEL"],
            temperature=0.6,
            response_format={"type": "json_object"},
            messages=messages,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        return jsonify(data)
    except json.JSONDecodeError:
        return jsonify({
            "error": "Model returned malformed JSON. Try again.",
        }), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = 8080
    app.run(host="0.0.0.0", port=port)