import json
from datetime import datetime
from collections import Counter

LOG_FILE = "logs.json"

# -----------------------------
# LOAD LOGS
# -----------------------------
def load_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "messages": [],
            "word_counts": {},
            "blocked_sources": {}
        }

# -----------------------------
# SAVE LOGS
# -----------------------------
def save_logs(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -----------------------------
# CHECK IF BLOCKED
# -----------------------------
def is_blocked(site):
    data = load_logs()
    return data.get("blocked_sources", {}).get(site, 0) >= 3

# -----------------------------
# UPDATE LOGS
# -----------------------------
def update_logs(message, prediction, source="SMS", site="unknown"):
    data = load_logs()

    # Normalize prediction (VERY IMPORTANT)
    prediction = prediction.lower()

    # 1. Store message
    data["messages"].append({
        "text": message,
        "prediction": prediction,
        "source": source,
        "site": site,
        "time": str(datetime.now())
    })

    # 2. Update word counts
    words = message.lower().split()
    word_count = Counter(words)

    for word, count in word_count.items():
        data["word_counts"][word] = data["word_counts"].get(word, 0) + count

    # 3. 🔥 Track malicious sources (FIXED)
    if prediction == "spam":
        data["blocked_sources"][site] = data["blocked_sources"].get(site, 0) + 1

    # 4. Save
    save_logs(data)