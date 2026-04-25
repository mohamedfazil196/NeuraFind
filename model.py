"""
model.py — Priority-Based Ensemble ML Recommendation Engine
User picks: budget + what they care about (camera, battery, performance…)
Engine maps priorities → feature weights → weighted cosine + KNN + RF scoring
Returns TOP 3 best matches with radar data.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor

# ─── Priority → Feature Weight Maps ─────────────────────────────────────────
#  Each priority boosts certain feature columns in the scoring.
#  Higher weight = that column matters more.

PRIORITY_WEIGHTS = {
    "mobile": {
        "camera":      {"camera": 6.0, "ram": 1.0, "storage": 1.0, "battery": 1.0, "rating": 2.0},
        "battery":     {"battery": 6.0, "ram": 1.0, "storage": 1.0, "camera": 1.0, "rating": 2.0},
        "performance": {"ram": 6.0, "storage": 4.0, "battery": 2.0, "camera": 1.0, "rating": 2.0},
        "gaming":      {"ram": 5.0, "battery": 4.0, "storage": 3.0, "camera": 1.0, "rating": 2.0},
        "selfie":      {"camera": 5.0, "ram": 2.0, "battery": 2.0, "storage": 2.0, "rating": 2.0},
        "value":       {"rating": 4.0, "ram": 2.0, "storage": 2.0, "camera": 2.0, "battery": 2.0},
        "5g":          {"ram": 2.0, "storage": 2.0, "battery": 2.0, "camera": 2.0, "rating": 3.0},
    },
    "laptop": {
        "performance": {"ram": 6.0, "storage": 4.0, "vram": 3.0, "battery_hours": 1.0, "rating": 2.0, "display_size": 1.0, "weight": 1.0},
        "gaming":      {"vram": 6.0, "ram": 5.0, "storage": 3.0, "display_size": 2.0, "battery_hours": 1.0, "rating": 2.0, "weight": 1.0},
        "battery":     {"battery_hours": 6.0, "weight": 3.0, "ram": 2.0, "storage": 1.0, "rating": 2.0, "vram": 1.0, "display_size": 1.0},
        "portability": {"weight": 6.0, "battery_hours": 4.0, "display_size": 3.0, "ram": 1.0, "storage": 1.0, "rating": 2.0, "vram": 1.0},
        "display":     {"display_size": 5.0, "ram": 2.0, "vram": 2.0, "battery_hours": 2.0, "storage": 1.0, "rating": 2.0, "weight": 1.0},
        "value":       {"rating": 4.0, "ram": 2.0, "storage": 2.0, "vram": 2.0, "battery_hours": 2.0, "display_size": 1.0, "weight": 1.0},
        "programming": {"ram": 5.0, "storage": 4.0, "battery_hours": 4.0, "weight": 3.0, "vram": 2.0, "rating": 2.0, "display_size": 1.0},
    },
    "smartwatch": {
        "health":    {"health_features": 6.0, "rating": 3.0, "battery_life": 2.0, "display_size": 1.0, "waterproof_rating": 2.0, "gps": 2.0, "sleep_tracking": 2.0},
        "battery":   {"battery_life": 6.0, "health_features": 2.0, "gps": 1.0, "sleep_tracking": 1.0, "waterproof_rating": 1.0, "display_size": 1.0, "rating": 2.0},
        "fitness":   {"gps": 5.0, "health_features": 4.0, "battery_life": 3.0, "waterproof_rating": 3.0, "sleep_tracking": 2.0, "display_size": 1.0, "rating": 2.0},
        "design":    {"display_size": 5.0, "rating": 4.0, "health_features": 2.0, "battery_life": 2.0, "gps": 1.0, "sleep_tracking": 1.0, "waterproof_rating": 1.0},
        "sleep":     {"sleep_tracking": 6.0, "health_features": 4.0, "battery_life": 4.0, "gps": 1.0, "rating": 2.0, "display_size": 1.0, "waterproof_rating": 1.0},
        "value":     {"rating": 5.0, "health_features": 3.0, "battery_life": 3.0, "gps": 2.0, "sleep_tracking": 2.0, "display_size": 2.0, "waterproof_rating": 2.0},
        "waterproof":{"waterproof_rating": 6.0, "health_features": 2.0, "battery_life": 2.0, "gps": 2.0, "sleep_tracking": 1.0, "display_size": 1.0, "rating": 2.0},
    },
}

# All numeric feature columns per device type
FEATURE_COLS = {
    "mobile":     ["price", "ram", "storage", "camera", "battery", "rating"],
    "laptop":     ["price", "ram", "storage", "vram", "rating", "display_size", "weight", "battery_hours"],
    "smartwatch": ["price", "battery_life", "display_size", "health_features",
                   "waterproof_rating", "rating", "gps", "sleep_tracking"],
}

# Friendly display labels for radar chart
FEATURE_LABELS = {
    "ram":              "Performance",
    "storage":          "Storage",
    "camera":           "Camera",
    "battery":          "Battery",
    "rating":           "User Rating",
    "vram":             "GPU Power",
    "display_size":     "Display",
    "weight":           "Portability",
    "battery_hours":    "Battery Life",
    "battery_life":     "Battery Life",
    "health_features":  "Health",
    "waterproof_rating":"Waterproof",
    "gps":              "GPS",
    "sleep_tracking":   "Sleep Track",
}

# Ensemble weights
W_COSINE, W_KNN, W_RF = 0.40, 0.35, 0.25

# ─── Dataset cache ────────────────────────────────────────────────────────────
_cache: dict = {}

def _load(device_type: str) -> pd.DataFrame:
    if device_type not in _cache:
        df = pd.read_csv(f"datasets/{device_type}.csv")
        for col in df.columns:
            if col not in ("name", "brand", "processor"):
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        # For laptops: lighter weight = better portability → invert for scoring
        _cache[device_type] = df
    return _cache[device_type].copy()


# ─── Priority combiner ────────────────────────────────────────────────────────

def _combine_weights(device_type: str, priorities: list[str], features: list[str]) -> np.ndarray:
    """
    Merge weights for all selected priorities into one weight vector.
    If no priority selected → uniform weights.
    """
    p_map = PRIORITY_WEIGHTS.get(device_type, {})
    weight_vec = np.ones(len(features))   # default: all equal

    if not priorities:
        return weight_vec

    combined = {f: 0.0 for f in features}
    for p in priorities:
        pw = p_map.get(p, {})
        for f, w in pw.items():
            if f in combined:
                combined[f] = max(combined[f], w)  # take the max across priorities

    for i, f in enumerate(features):
        if combined.get(f, 0) > 0:
            weight_vec[i] = combined[f]

    return weight_vec


# ─── Spec formatter ───────────────────────────────────────────────────────────

def _build_specs(device_type: str, row: pd.Series) -> dict:
    base = {"Price": f"₹{int(row['price']):,}"}
    if device_type == "mobile":
        base.update({
            "RAM":     f"{int(row['ram'])} GB",
            "Storage": f"{int(row['storage'])} GB",
            "Camera":  f"{int(row['camera'])} MP",
            "Battery": f"{int(row['battery'])} mAh",
            "Rating":  f"⭐ {float(row['rating']):.1f} / 5",
        })
    elif device_type == "laptop":
        base.update({
            "RAM":        f"{int(row['ram'])} GB",
            "Storage":    f"{int(row['storage'])} GB",
            "GPU (VRAM)": f"{int(row['vram'])} GB",
            "Processor":  str(row.get("processor", "N/A")),
            "Display":    f"{float(row.get('display_size', 0)):.1f}\"",
            "Weight":     f"{float(row.get('weight', 0)):.1f} kg",
            "Battery":    f"{int(row.get('battery_hours', 0))} hrs",
            "Rating":     f"⭐ {float(row['rating']):.1f} / 5",
        })
    else:  # smartwatch
        base.update({
            "Battery Life":   f"{int(row['battery_life'])} days",
            "Display":        f"{float(row['display_size']):.2f}\"",
            "Health Score":   f"{int(row['health_features'])} / 10",
            "Waterproof":     f"IP{int(row['waterproof_rating'])}",
            "GPS":            "✅ Yes" if int(row.get("gps", 0)) else "❌ No",
            "Sleep Tracking": "✅ Yes" if int(row.get("sleep_tracking", 0)) else "❌ No",
            "Rating":         f"⭐ {float(row['rating']):.1f} / 5",
        })
    return base


# ─── Radar data ───────────────────────────────────────────────────────────────

def _build_radar(device_type: str, row: pd.Series, features: list[str],
                 data_matrix: np.ndarray, feat_idx: dict) -> dict:
    """Return normalised values 0-100 for each non-price feature (max 6 dims)."""
    radar_feats = [f for f in features if f != "price"][:6]
    labels, values = [], []

    col_data = data_matrix  # not yet scaled; use min/max from dataset
    for feat in radar_feats:
        if feat not in feat_idx:
            continue
        idx = feat_idx[feat]
        col = col_data[:, idx]
        col_min, col_max = col.min(), col.max()
        raw = float(row.get(feat, 0))

        # For weight (laptop) → lighter is better → invert
        if feat == "weight":
            raw_inv = col_max - raw + col_min
            raw = raw_inv

        rng = col_max - col_min if col_max != col_min else 1
        norm = min(max((raw - col_min) / rng, 0), 1) * 100
        labels.append(FEATURE_LABELS.get(feat, feat.replace("_", " ").title()))
        values.append(round(norm, 1))

    return {"labels": labels, "values": values}


# ─── Ensemble scorer ──────────────────────────────────────────────────────────

def _ensemble_score(data_sc: np.ndarray, user_sc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = len(data_sc)
    cos_sc = cosine_similarity(user_sc, data_sc)[0]

    if n >= 3:
        knn = KNeighborsRegressor(n_neighbors=min(5, n), metric="cosine")
        knn.fit(data_sc, cos_sc)
        knn_sc = np.clip(knn.predict(data_sc), 0, 1)
    else:
        knn_sc = cos_sc.copy()

    if n >= 5:
        rf = RandomForestRegressor(n_estimators=60, random_state=42, n_jobs=-1)
        rf.fit(data_sc, cos_sc)
        rf_sc = np.clip(rf.predict(data_sc), 0, 1)
    else:
        rf_sc = cos_sc.copy()

    ensemble = W_COSINE * cos_sc + W_KNN * knn_sc + W_RF * rf_sc
    std = np.std(np.vstack([cos_sc, knn_sc, rf_sc]), axis=0)
    confidence = 1.0 - np.clip(std * 4, 0, 1)
    return ensemble, confidence


# ─── Why-this-device reason ───────────────────────────────────────────────────

def _make_reason(priorities: list[str], device_type: str, row: pd.Series) -> str:
    if not priorities:
        return "Excellent all-round match for your budget and requirements."

    p_map = PRIORITY_WEIGHTS.get(device_type, {})
    top_feats = []
    for p in priorities[:2]:
        pw = p_map.get(p, {})
        best_f = max(pw, key=pw.get, default=None)
        if best_f:
            top_feats.append(FEATURE_LABELS.get(best_f, best_f.replace("_", " ").title()))

    p_labels = {
        "camera": "camera quality", "battery": "battery life",
        "performance": "raw performance", "gaming": "gaming capability",
        "selfie": "selfie camera", "value": "value for money",
        "5g": "5G connectivity", "programming": "developer workflow",
        "portability": "portability", "display": "display quality",
        "health": "health monitoring", "fitness": "fitness tracking",
        "sleep": "sleep tracking", "design": "design & display",
        "waterproof": "water resistance",
    }
    chosen = " & ".join(p_labels.get(p, p) for p in priorities[:2])
    rating = float(row.get("rating", 0))
    return f"Top pick for {chosen}, rated ⭐ {rating:.1f}/5 by real users."


# ─── Main recommend function ──────────────────────────────────────────────────

def recommend(device_type: str, budget: float, priorities: list[str],
              brand: str = "") -> list[dict]:
    """
    Priority-based ensemble recommendation.

    Parameters
    ----------
    device_type : "mobile" | "laptop" | "smartwatch"
    budget      : max price in ₹
    priorities  : list of priority keys e.g. ["camera", "battery"]
    brand       : optional brand preference

    Returns top-3 dicts: name, brand, score, confidence, specs, reason, radar
    """
    df       = _load(device_type)
    
    preferred_brand = brand.strip().lower()
    
    # Strict Brand Filter
    if preferred_brand:
        brand_df = df[df["brand"].str.lower() == preferred_brand]
        if not brand_df.empty:
            df = brand_df  # Now only contains that brand
            
    features = FEATURE_COLS[device_type]
    feat_idx = {f: i for i, f in enumerate(features)}

    # ── Budget filter ────────────────────────────────────────────────────────
    filtered = df[df["price"] <= budget].copy()
    
    # If explicitly 0 devices match the budget and brand, just return the absolute cheapest ones available
    if filtered.empty:
        filtered = df.nsmallest(min(15, len(df)), "price").copy()

    raw_matrix = filtered[features].values.astype(float)  # for radar

    # ── Build priority weight vector ─────────────────────────────────────────
    w = _combine_weights(device_type, priorities, features)

    # Price feature: always penalise — user wants best specs within budget
    price_idx = feat_idx.get("price", 0)
    w[price_idx] = 0.5   # low weight on price (budget filter already handles it)

    # ── Apply weights to data matrix ─────────────────────────────────────────
    weighted_matrix = raw_matrix * w

    # ── Build user ideal vector ───────────────────────────────────────────────
    # User ideal = maximum possible in each weighted dimension
    user_ideal = np.max(weighted_matrix, axis=0).reshape(1, -1)

    # ── Scale ────────────────────────────────────────────────────────────────
    scaler      = MinMaxScaler()
    combined_sc = scaler.fit_transform(np.vstack([weighted_matrix, user_ideal]))
    data_sc     = combined_sc[:-1]
    user_sc     = combined_sc[-1].reshape(1, -1)

    # ── Ensemble scoring ──────────────────────────────────────────────────────
    scores, conf = _ensemble_score(data_sc, user_sc)

    # Brand bonus
    preferred_brand = brand.strip().lower()

    # Sort by score, return top-3
    top_idx = np.argsort(scores)[::-1][:3]

    results = []
    for idx in top_idx:
        row   = filtered.iloc[idx]
        score = float(scores[idx])
        c     = float(conf[idx])

        if preferred_brand and str(row.get("brand", "")).lower() == preferred_brand:
            score = min(score + 0.05, 1.0)

        results.append({
            "name":       str(row["name"]),
            "brand":      str(row.get("brand", "")),
            "score":      round(score * 100, 1),
            "confidence": round(c * 100, 1),
            "specs":      _build_specs(device_type, row),
            "reason":     _make_reason(priorities, device_type, row),
            "radar":      _build_radar(device_type, row, features, raw_matrix, feat_idx),
        })

    return results
