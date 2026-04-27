"""
app.py — NeuraFind V2 Advanced AI Device Recommender
Routes: /recommend, /chat, /market-insight, /compare, /history
V2: Real-time Gemini-first recommendations with ML fallback
V2.1: Supabase PostgreSQL for persistent production-grade history
"""

import os
import uuid
import secrets
from flask import Flask, render_template, request, jsonify, make_response
from dotenv import load_dotenv

from model import recommend
from gemini_client import (
    explain_recommendation, chat as gemini_chat, market_insight,
    get_realtime_recommendations, get_live_pick, get_standalone_insights
)

# Initialize Supabase (optional, falls back to memory if not configured)
load_dotenv(override=True)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"[NeuraFind] ✅ Supabase connected to {SUPABASE_URL}")
    except Exception as e:
        print(f"[NeuraFind] ❌ Supabase init error: {e}")
else:
    print("[NeuraFind] ⚠️ Supabase credentials missing. History will be temporary (in-memory).")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# In-memory fallback if Supabase is not configured
_memory_history = {}


def _get_or_create_user_id(req):
    """Retrieve anon_id from cookies or generate a new one."""
    anon_id = req.cookies.get("neurafind_anon_id")
    if not anon_id:
        anon_id = str(uuid.uuid4())
    return anon_id


def _save_history(user_id, device_type, budget, priorities, results):
    """Save search history to Supabase or fallback memory."""
    top_result = results[0]["name"] if results else "N/A"
    score = results[0].get("score", 0) if results else 0
    
    entry = {
        "user_id": user_id,
        "device_type": device_type,
        "budget": budget,
        "priorities": priorities if isinstance(priorities, list) else [],
        "top_result": top_result,
        "score": score,
        "result_count": len(results)
    }

    if supabase_client:
        try:
            print(f"[NeuraFind] Saving history for user {user_id}...")
            res = supabase_client.table("search_history").insert(entry).execute()
            print(f"[NeuraFind] ✅ History saved to Supabase: {res.data}")
        except Exception as e:
            print(f"[NeuraFind] ❌ Failed to save history to Supabase: {e}")
    else:
        # Fallback to memory
        if user_id not in _memory_history:
            _memory_history[user_id] = []
        import datetime
        entry["created_at"] = datetime.datetime.now().isoformat()
        _memory_history[user_id].insert(0, entry)
        _memory_history[user_id] = _memory_history[user_id][:20]
        print(f"[NeuraFind] ⚠️ History saved to memory for user {user_id}")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    resp = make_response(render_template("index.html"))
    # Ensure every user gets an anonymous tracking ID cookie for history
    if not request.cookies.get("neurafind_anon_id"):
        resp.set_cookie("neurafind_anon_id", str(uuid.uuid4()), max_age=60*60*24*365) # 1 year
    return resp


@app.route("/recommend", methods=["POST"])
def get_recommendations():
    try:
        user_id = _get_or_create_user_id(request)
        data = request.get_json(force=True)
        
        device_type = data.get("device_type", "").strip().lower()
        budget      = float(data.get("budget", 30000))
        priorities  = data.get("priorities", [])
        brand       = data.get("brand", "")

        # V2 lifestyle fields
        usage           = data.get("usage", "general")
        gaming          = data.get("gaming", "no")
        travel          = data.get("travel", "no")
        camera_priority = data.get("camera_priority", "medium")

        if device_type not in ("mobile", "laptop", "smartwatch"):
            return jsonify({"error": "Invalid device type."}), 400

        # ── PRIMARY: Real-time Gemini recommendations ─────────────────────
        realtime = get_realtime_recommendations(
            device_type, budget, priorities, brand,
            usage, gaming, travel, camera_priority,
        )

        if realtime and realtime.get("recommendations"):
            results = realtime["recommendations"]
            results.sort(key=lambda x: x.get("score", 0), reverse=True)

            _save_history(user_id, device_type, budget, priorities, results)

            resp = make_response(jsonify({
                "recommendations": results,
                "personality":     realtime.get("personality", {}),
                "tradeoff":        realtime.get("tradeoff", {}),
                "ai_powered":      True,
                "source":          "realtime",
            }))
            resp.set_cookie("neurafind_anon_id", user_id, max_age=60*60*24*365)
            return resp

        # ── FALLBACK: Local ML engine ─────────────────────────────────────
        print("[NeuraFind] Real-time unavailable — falling back to ML engine")
        results = recommend(device_type, budget, priorities, brand)

        results_subset = results[:2]
        exclude_names = []
        for i, res in enumerate(results_subset):
            exclude_names.append(res["name"])
            explanation = explain_recommendation(
                device_name=res["name"],
                specs=res["specs"],
                user_prefs={"budget": budget, "priorities": ", ".join(priorities)},
                device_type=device_type,
                score=res["score"],
            )
            results_subset[i]["gemini_explanation"] = explanation

        live_picks = get_live_pick(device_type, budget, priorities, brand, exclude_names)

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

        results = results_subset
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Generate insights for fallback path (V2.1)
        insights = get_standalone_insights(device_type, budget, priorities, results[0]["name"] if results else "N/A")

        _save_history(user_id, device_type, budget, priorities, results)

        resp = make_response(jsonify({
            "recommendations": results,
            "personality":     insights.get("personality", {}),
            "tradeoff":        insights.get("tradeoff", {}),
            "ai_powered":      True,
            "source":          "dataset",
        }))
        resp.set_cookie("neurafind_anon_id", user_id, max_age=60*60*24*365)
        return resp

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


@app.route("/history", methods=["GET"])
def history_endpoint():
    user_id = _get_or_create_user_id(request)
    
    formatted_history = []
    if supabase_client:
        try:
            print(f"[NeuraFind] Fetching history for user {user_id}...")
            response = supabase_client.table("search_history") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(20) \
                .execute()
            history = response.data
            
            for item in history:
                formatted_history.append({
                    "device_type": item["device_type"],
                    "budget": item["budget"],
                    "priorities": item.get("priorities", []),
                    "top_result": item["top_result"],
                    "score": item["score"],
                    "count": item["result_count"]
                })
        except Exception as e:
            print(f"[NeuraFind] ❌ Failed to load history from Supabase: {e}")
    else:
        formatted_history = _memory_history.get(user_id, [])

    resp = make_response(jsonify({"history": formatted_history}))
    # Ensure the user gets the cookie if they didn't have it (e.g. direct access)
    if not request.cookies.get("neurafind_anon_id"):
        resp.set_cookie("neurafind_anon_id", user_id, max_age=60*60*24*365)
    return resp


if __name__ == "__main__":
    app.run(debug=True, port=5000)
