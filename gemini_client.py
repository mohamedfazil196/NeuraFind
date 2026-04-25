"""
gemini_client.py — Google Gemini AI Integration
Provides three capabilities:
  1. explain_recommendation → Natural language explanation for a device match
  2. chat                   → Conversational AI assistant for device buying advice
  3. market_insight         → Category-level AI market analysis
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

from dotenv import load_dotenv

def _get_model():
    """Lazily initialise and return the Gemini model."""
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    
    if not api_key or api_key == "your_gemini_api_key_here" or api_key.startswith("your_"):
        return None
        
    genai.configure(api_key=api_key)
    # Using 2.5-flash-lite to bypass strict quota limits
    return genai.GenerativeModel("gemini-2.5-flash-lite")


# ─── 1. Device Recommendation Explanation ────────────────────────────────────

def explain_recommendation(device_name: str, specs: dict, user_prefs: dict,
                            device_type: str, score: float) -> str:
    """
    Generate a 2-3 sentence natural-language explanation of WHY this device
    was recommended, tailored to the user's stated preferences.

    Falls back to a rule-based string if no API key is set.
    """
    model = _get_model()
    if model is None:
        return _fallback_explanation(device_name, specs, user_prefs, score)

    budget = user_prefs.get("budget", 0)
    specs_str = ", ".join(f"{k}: {v}" for k, v in specs.items())
    prefs_str = ", ".join(f"{k}: {v}" for k, v in user_prefs.items() if k != "brand")

    prompt = (
        f"You are an expert tech advisor. Explain in exactly 2-3 concise sentences "
        f"why the {device_type} '{device_name}' (match score: {score:.1f}%) is a great choice "
        f"for a user with these preferences: {prefs_str}. "
        f"The device specs are: {specs_str}. "
        f"Be specific, enthusiastic, and mention real value propositions. "
        f"Do NOT use bullet points. Plain paragraph only."
    )

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return _fallback_explanation(device_name, specs, user_prefs, score)


def _fallback_explanation(device_name: str, specs: dict, user_prefs: dict,
                           score: float) -> str:
    """Rule-based fallback when no Gemini key is configured."""
    budget = float(user_prefs.get("budget", 0))
    price_str = specs.get("Price", "")
    top_specs = list(specs.items())[1:3]
    spec_highlight = " and ".join(f"{k} of {v}" for k, v in top_specs)
    return (
        f"{device_name} scores {score:.1f}% compatibility with your requirements, "
        f"offering {spec_highlight}. "
        f"It represents excellent value within your ₹{int(budget):,} budget."
    )


# ─── 2. Conversational Chat Assistant ─────────────────────────────────────────

def chat(conversation_history: list[dict], user_message: str) -> str:
    """
    Continue a multi-turn conversation about device buying.

    conversation_history: list of {"role": "user"|"model", "parts": [str]}
    user_message: the latest user query
    """
    model = _get_model()
    if model is None:
        return (
            "🔑 Gemini API key not configured. Please add your GEMINI_API_KEY to the .env file. "
            "Get a free key at https://aistudio.google.com/app/apikey"
        )

    system_context = (
        "You are NeuraBot, an expert AI device advisor specialising in mobiles, laptops, "
        "and smartwatches. You give concise, data-driven, friendly advice. "
        "When recommending devices, mention specific model names and real prices in Indian Rupees (₹). "
        "Keep answers under 150 words unless the user asks for a detailed comparison."
    )

    # Build conversation for Gemini multi-turn
    chat_session = model.start_chat(history=conversation_history)

    try:
        response = chat_session.send_message(
            f"[System: {system_context}]\n\nUser: {user_message}"
        )
        return response.text.strip()
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"


# ─── 3. Market Insight / Buying Guide ─────────────────────────────────────────

def market_insight(category: str, budget: float) -> dict:
    """
    Generate an AI-powered market analysis and buying guide for a device category.

    Returns a dict with keys: summary, hot_picks, avoid, pro_tip
    """
    model = _get_model()
    if model is None:
        return _fallback_market_insight(category, budget)

    budget_label = f"₹{int(budget):,}" if budget > 0 else "any budget"

    prompt = f"""You are a senior tech market analyst. For the {category} market at {budget_label} budget in India (2025):

Return a JSON object with exactly these 4 keys:
1. "summary": 2 sentence market overview
2. "hot_picks": array of 3 specific model name strings that are popular right now
3. "avoid": one short sentence about what to watch out for in this category/budget
4. "pro_tip": one actionable buying tip (1 sentence)

Respond with ONLY valid JSON, no markdown, no explanation."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        import json
        return json.loads(text.strip())
    except Exception:
        return _fallback_market_insight(category, budget)


def _fallback_market_insight(category: str, budget: float) -> dict:
    insights = {
        "mobile": {
            "summary": "The Indian smartphone market in 2025 is dominated by 5G devices at every budget tier. Brands like Xiaomi, Samsung, and Nothing are delivering exceptional value.",
            "hot_picks": ["Nothing Phone 2a", "OnePlus Nord CE5", "Samsung Galaxy A56 5G"],
            "avoid": "Avoid devices with less than 6GB RAM — they struggle with modern apps and updates.",
            "pro_tip": "For the best camera experience on a budget, look for phones with 200MP sensors or Google's computational photography."
        },
        "laptop": {
            "summary": "2025 laptops are all about efficiency — Apple Silicon and AMD Ryzen 8000 series dominate. Gaming laptops now offer desktop-class GPUs at record lows.",
            "hot_picks": ["Apple MacBook Air M3", "ASUS ROG Zephyrus G16", "Lenovo ThinkPad X1 Carbon"],
            "avoid": "Avoid laptops with less than 16GB RAM if you plan to run modern AI tools or multitask heavily.",
            "pro_tip": "For developers and creators, Apple M3 chips offer the best performance-per-watt by a significant margin."
        },
        "smartwatch": {
            "summary": "The smartwatch segment has matured with health features now standard from ₹5K onwards. Apple and Samsung lead, but Garmin dominates fitness enthusiasts.",
            "hot_picks": ["Apple Watch Series 9", "Samsung Galaxy Watch 6", "Garmin Forerunner 265"],
            "avoid": "Avoid basic budget smartwatches that lack ECG or blood oxygen sensors — they add little over a fitness band.",
            "pro_tip": "For serious athletes, invest in a Garmin — their GPS accuracy and battery life are unmatched by Apple or Samsung."
        }
    }
    cat = category.lower().replace("smartwatch", "smartwatch")
    if "watch" in cat:
        cat = "smartwatch"
    return insights.get(cat, insights["mobile"])


# ─── 4. Live AI Recommendation (Outside Dataset) ──────────────────────────────

def get_live_pick(device_type: str, budget: float, priorities: list[str], brand: str, exclude_names: list[str]) -> list[dict]:
    """Uses Gemini to find real-world devices NOT in the dataset."""
    model = _get_model()
    if model is None:
        return []

    priorities_str = ", ".join(priorities) if priorities else "balanced performance"
    exclude_str = ", ".join(exclude_names) if exclude_names else "none"

    prompt = f"""You are an expert tech advisor. A user is looking for a {device_type} in India (2024/2025).
Budget: strictly under ₹{budget}
Priorities: {priorities_str}
Brand preference: {brand if brand else "Any"}

Find ONE real-world {device_type} that perfectly matches these criteria.
It MUST NOT be any of these devices: {exclude_str}.

Respond strictly with a JSON object matching this schema exactly:
{{
  "name": "Full precise model name",
  "brand": "Brand name",
  "score": 98.5,
  "confidence": 95.0,
  "specs": {{
    "Price": "₹XX,XXX",
    "Key Spec 1": "Value",
    "Key Spec 2": "Value",
    "Key Spec 3": "Value",
    "Key Spec 4": "Value"
  }},
  "reason": "One sentence explaining why it's recommended based on their priorities.",
  "radar": {{
    "labels": ["Performance", "Camera", "Battery", "Display", "Value", "Design"],
    "values": [90, 85, 88, 92, 85, 80]
  }},
  "gemini_explanation": "2-3 sentences explaining why this live AI pick is perfect for them.",
  "is_live_gemini": true
}}

Ensure radar values are between 0 and 100. DO NOT wrap JSON in markdown block. Return raw JSON.
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        import json
        pick = json.loads(text.strip())
        return [pick]
    except Exception as e:
        print(f"Gemini live pick error: {e}")
        return []
