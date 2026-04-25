"""
app.py — NeuraFind Advanced AI Device Recommender
Routes: /recommend, /chat, /market-insight, /compare, /history
"""

from flask import Flask, render_template, request, jsonify, session
import secrets
from model import recommend
from gemini_client import explain_recommendation, chat as gemini_chat, market_insight

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


def _save_history(device_type, budget, priorities, results):
    if "history" not in session:
        session["history"] = []
    entry = {
        "device_type": device_type,
        "budget":      budget,
        "priorities":  priorities,
        "top_result":  results[0]["name"] if results else "N/A",
        "score":       results[0]["score"] if results else 0,
        "count":       len(results),
    }
    session["history"] = ([entry] + session["history"])[:10]
    session.modified = True


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/recommend", methods=["POST"])
def get_recommendations():
    """
    Body: { device_type, budget, priorities: [...], brand }
    Returns: { recommendations: [top-3], ai_powered: bool }
    """
    try:
        data        = request.get_json(force=True)
        device_type = data.get("device_type", "").strip().lower()
        budget      = float(data.get("budget", 30000))
        priorities  = data.get("priorities", [])
        brand       = data.get("brand", "")

        if device_type not in ("mobile", "laptop", "smartwatch"):
            return jsonify({"error": "Invalid device type."}), 400

        results = recommend(device_type, budget, priorities, brand)

        # Gemini explanation for all top-2 from dataset
        results_subset = results[:2] # Keep top 2 from dataset
        exclude_names = []
        for i, res in enumerate(results_subset):
            exclude_names.append(res['name'])
            explanation = explain_recommendation(
                device_name=res["name"],
                specs=res["specs"],
                user_prefs={"budget": budget, "priorities": ", ".join(priorities)},
                device_type=device_type,
                score=res["score"],
            )
            results_subset[i]["gemini_explanation"] = explanation

        # Get 1 live pick from Gemini
        from gemini_client import get_live_pick
        live_picks = get_live_pick(device_type, budget, priorities, brand, exclude_names)
        
        # If Gemini returned something, use it as the 3rd. Otherwise fallback to the 3rd best local result.
        if live_picks:
            results_subset.extend(live_picks)
        elif len(results) > 2:
            res_3 = results[2]
            res_3["gemini_explanation"] = explain_recommendation(
                device_name=res_3["name"],
                specs=res_3["specs"],
                user_prefs={"budget": budget, "priorities": ", ".join(priorities)},
                device_type=device_type,
                score=res_3["score"],
            )
            results_subset.append(res_3)

        # Re-assign back to results before sorting
        results = results_subset
        
        # Sort by score just in case
        results.sort(key=lambda x: x.get('score', 0), reverse=True)

        _save_history(device_type, budget, priorities, results)

        return jsonify({"recommendations": results, "ai_powered": True})

    except Exception as exc:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data    = request.get_json(force=True)
    message = data.get("message", "").strip()
    history = data.get("history", [])
    if not message:
        return jsonify({"error": "Empty message."}), 400
    reply = gemini_chat(history, message)
    return jsonify({"reply": reply})


@app.route("/market-insight", methods=["POST"])
def market_insight_endpoint():
    data     = request.get_json(force=True)
    category = data.get("category", "mobile")
    budget   = float(data.get("budget", 0))
    insight  = market_insight(category, budget)
    return jsonify(insight)


@app.route("/compare", methods=["POST"])
def compare_endpoint():
    import pandas as pd
    data        = request.get_json(force=True)
    device_type = data.get("device_type", "mobile")
    names       = data.get("devices", [])
    df = pd.read_csv(f"datasets/{device_type}.csv")
    comparison = {}
    for name in names:
        row = df[df["name"] == name]
        if not row.empty:
            from model import _build_specs
            comparison[name] = _build_specs(device_type, row.iloc[0])
    return jsonify({"comparison": comparison})


@app.route("/history", methods=["GET"])
def history_endpoint():
    return jsonify({"history": session.get("history", [])})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
