import os
from dotenv import load_dotenv
load_dotenv()

from gemini_client import get_live_pick

print("Testing get_live_pick...")
try:
    res = get_live_pick("mobile", 20000, ["camera", "battery"], "Xiaomi", [])
    print("Result:", res)
except Exception as e:
    print("Top-level Error:", e)
