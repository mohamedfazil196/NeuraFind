# 🤖 Smart AI Device Recommender

A **production-style AI/ML web application** that recommends the best Mobile, Laptop, or Smartwatch based on your preferences using **Cosine Similarity** and **MinMaxScaler**.

---

## ✨ Features

| Feature | Detail |
|---|---|
| 🧠 ML Engine | Cosine Similarity + MinMaxScaler (scikit-learn) |
| 📱💻⌚ Devices | Mobile · Laptop · Smartwatch |
| 🎨 UI | Premium dark glassmorphism SaaS design |
| ⚡ Stack | Python · Flask · Vanilla JS · CSS3 |
| 📊 Data | 3 curated CSVs with 10 realistic devices each |
| 🏷️ Results | Top-5 cards with Match %, specs, and AI reason |

---

## 📁 Project Structure

```
device-recommender/
├── app.py              ← Flask routes
├── model.py            ← ML engine (cosine similarity)
├── requirements.txt    ← Python deps
├── datasets/
│   ├── mobile.csv
│   ├── laptop.csv
│   └── smartwatch.csv
├── templates/
│   └── index.html      ← Single-page UI
└── static/
    ├── style.css       ← Premium dark theme
    └── script.js       ← Dynamic form + API calls
```

---

## 🚀 Installation & Run

### 1. Clone / enter the project folder
```bash
cd device-recommender
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Flask server
```bash
python app.py
```

### 5. Open your browser
```
http://localhost:5000
```

---

## 🧠 How the ML Works

1. **Load** the correct dataset (mobile / laptop / smartwatch CSV)  
2. **Budget filter** — keep devices within 1.4× the user's budget  
3. **Vectorise** — extract numeric feature columns  
4. **MinMaxScaler** — normalise dataset + user vector together [0, 1]  
5. **Cosine Similarity** — measure angular similarity between user vector and each device  
6. **Brand bonus** — small +5% lift if preferred brand matches  
7. **Return Top-5** with match %, key specs, and reason string  

---

## 🎨 UI Design Highlights

- **Background**: Deep space gradient `#020617 → #0f172a` with animated radial glows  
- **Cards**: Glassmorphism (backdrop-filter blur + semi-transparent bg)  
- **Accents**: Indigo `#6366f1` · Violet `#8b5cf6` · Cyan `#06b6d4`  
- **Typography**: Syne (display, headings) + DM Sans (body)  
- **Animations**: Staggered card entrance, animated score bars, pulsing badge dot  
- **Hover states**: Lift + glow on all interactive elements  

---

## 📸 UI Description

```
┌─────────────────────────────────────────────┐
│  · AI-Powered · ML Recommendations          │
│                                             │
│   Smart AI Device                           │
│   Recommender                               │
│   Find your perfect device, powered by AI  │
├─────────────────────────────────────────────┤
│  SELECT DEVICE CATEGORY                     │
│  [ 📱 Mobile ] [ 💻 Laptop ] [ ⌚ Smartwatch] │
│  ─────────────────────────────────────────  │
│  YOUR PREFERENCES                           │
│  ┌──────────┐ ┌──────────┐                  │
│  │ Budget   │ │ RAM      │                  │
│  └──────────┘ └──────────┘                  │
│  ┌──────────┐ ┌──────────┐                  │
│  │ Storage  │ │ Camera   │                  │
│  └──────────┘ └──────────┘                  │
│  ┌──────────┐ ┌──────────┐                  │
│  │ Battery  │ │ Brand ▼  │                  │
│  └──────────┘ └──────────┘                  │
│                                             │
│  [ ✦  Find Best Matches  ]                  │
└─────────────────────────────────────────────┘

TOP RECOMMENDATIONS           5 matches found
┌─────────────────────────────────┐  #1
│ Samsung Galaxy A54              │
│ SAMSUNG                         │
│ Match Score ████████░░  76.3%   │
│ [Price ₹38,999][RAM 8 GB]...    │
│ ✦ High match due to battery...  │
└─────────────────────────────────┘
```
