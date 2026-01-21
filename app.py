from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import math

app = Flask(__name__)
CORS(app)

DATA_FILE = "places_kaggle.json"  # created by prepare_data.py


# ---------- Helpers ----------
def load_places():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def budget_level(budget):
    if budget <= 1500:
        return "low"
    elif budget <= 4000:
        return "medium"
    return "high"


def score_place(place, interests, level):
    """
    AI-like scoring using:
    - interest match (category text)
    - google review rating
    - budget preference (entrance fee)
    """
    score = 0.0

    category = str(place.get("category", "")).lower()
    rating = float(place.get("rating", 0) or 0)
    cost = int(place.get("avg_cost", 0) or 0)

    # 1) Interest match (strong)
    for intr in interests:
        intr = str(intr).lower().strip()
        if intr and intr in category:
            score += 6

    # 2) Rating boost (0-5 -> 0-10)
    score += rating * 2

    # 3) Budget preference
    if level == "low":
        if cost == 0:
            score += 4
        elif cost <= 50:
            score += 3
        elif cost <= 150:
            score += 1
        else:
            score -= 2
    elif level == "medium":
        if cost <= 200:
            score += 2
        elif cost <= 500:
            score += 1
        else:
            score -= 1
    else:
        score += 1

    return score


def total_places_cost(places):
    return sum(int(p.get("avg_cost", 0) or 0) for p in places)


def make_itinerary(selected, days):
    itinerary = []
    if days <= 0:
        days = 1

    # approx max 3 places per day
    per_day = max(1, math.ceil(len(selected) / days))
    idx = 0

    for d in range(1, days + 1):
        day_places = selected[idx: idx + per_day]
        if not day_places:
            break
        itinerary.append({"day": d, "places": day_places})
        idx += per_day

    return itinerary


def estimate_other_costs(level, days):
    """
    student-friendly estimation for:
    - food
    - local travel
    - stay
    - misc
    """
    if level == "low":
        food_per_day = 250
        local_travel_per_day = 150
        stay_per_night = 0 if days == 1 else 400
    elif level == "medium":
        food_per_day = 400
        local_travel_per_day = 250
        stay_per_night = 0 if days == 1 else 700
    else:
        food_per_day = 650
        local_travel_per_day = 350
        stay_per_night = 0 if days == 1 else 1200

    food = food_per_day * days
    local_travel = local_travel_per_day * days
    nights = max(0, days - 1)
    stay = stay_per_night * nights
    misc = 300

    return food, local_travel, stay, misc


# ---------- Routes ----------
@app.route("/", methods=["GET"])
def home():
    return "AI Travel Planner Backend Running ✅"


@app.route("/cities", methods=["GET"])
def get_cities():
    places = load_places()
    cities = sorted(list({p.get("city", "") for p in places if p.get("city", "")}))
    return jsonify({"cities": cities})


@app.route("/plan", methods=["POST"])
def plan_trip():
    data = request.get_json() or {}

    city = str(data.get("city", "")).strip()
    days = int(data.get("days", 1) or 1)
    budget = int(data.get("budget", 1000) or 1000)
    interests = data.get("interests", [])
    if not isinstance(interests, list):
        interests = []

    all_places = load_places()

    # Filter by city (case-insensitive)
    city_places = [p for p in all_places if str(p.get("city", "")).lower() == city.lower()]

    if not city_places:
        sample_cities = sorted(list({p.get("city", "") for p in all_places if p.get("city", "")}))[:10]
        return jsonify({
            "error": f"No places found for city '{city}'. Example cities: {', '.join(sample_cities)}"
        }), 400

    level = budget_level(budget)

    # Rank places
    scored = [(score_place(p, interests, level), p) for p in city_places]
    scored.sort(key=lambda x: x[0], reverse=True)
    ranked = [p for _, p in scored]

    # select max 3 places/day
    max_places = min(len(ranked), days * 3)
    selected = ranked[:max_places]

    # Budget optimization on places entry-fee
    removed = []
    while total_places_cost(selected) > budget and len(selected) > 1:
        selected.sort(key=lambda x: int(x.get("avg_cost", 0) or 0), reverse=True)
        removed_place = selected.pop(0)
        removed.append(str(removed_place.get("name", "")))

    itinerary = make_itinerary(selected, days)

    places_cost = total_places_cost(selected)
    food, local_travel, stay, misc = estimate_other_costs(level, days)
    total_est = places_cost + food + local_travel + stay + misc

    # AI summary
    summary = f"I generated a {days}-day plan for {city} using Kaggle dataset and interest+rating ranking."
    if level == "low":
        summary += " Since your budget is low, I prioritized free/low-fee places."
    elif level == "medium":
        summary += " I balanced top-rated attractions with affordable options."
    else:
        summary += " Your budget allows more flexibility, so I included more top-rated places."

    if removed:
        summary += f" To match your budget, I removed some high-fee places (ex: {', '.join(removed[:2])})."

    return jsonify({
        "city": city,
        "days": days,
        "budget": budget,
        "budget_level": level,
        "message": "Plan generated using AI-like ranking (interest + Google rating) and budget optimization.",
        "ai_summary": summary,
        "cost_breakup": {
            "places_tickets": places_cost,
            "food": food,
            "local_travel": local_travel,
            "stay": stay,
            "misc": misc,
            "total_estimated": total_est
        },
        "itinerary": itinerary
    })


if __name__ == "__main__":
    app.run(debug=True)
