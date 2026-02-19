
# ---------- IMPORTS ----------
import re
import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import mysql.connector
from fastapi import FastAPI, HTTPException

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- APP ----------
app = FastAPI(title="Hotel Review Analysis POC", version="1.0")

# ---------- CONSTANTS ----------
MODEL_NAME = "mock-llm-v1"
PROMPT_VERSION = "v1.0"

# ---------- MYSQL CONFIG ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "heyimlearning12",
    "database": "review_poc",
}

# ---------- REGEX PATTERNS ----------
PRICE_REGEX = r"(₹|rs\.?|inr|\b\d{4,6}\b)"
PHONE_REGEX = r"\b\d{10}\b"
EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
LINK_REGEX = r"(http://|https://|www\.)"
ABUSIVE_REGEX = r"(idiot|stupid|worst|shit|fuck|bastard)"
OWNER_REGEX = r"(owner|manager|mr\.?\s?[a-z]+)"

# ---------- TAG DEFINITIONS ----------
TOPIC_TAGS = {
    "clean": "CLEANLINESS",
    "room": "ROOM_QUALITY",
    "bathroom": "BATHROOM",
    "breakfast": "FOOD_BREAKFAST",
    "food": "RESTAURANT_FOOD",
    "staff": "SERVICE_STAFF",
    "check": "CHECKIN_CHECKOUT",
    "location": "LOCATION",
    "pool": "AMENITIES",
    "gym": "AMENITIES",
    "wifi": "WIFI",
    "noise": "NOISE",
    "parking": "PARKING",
    "safe": "SAFETY_SECURITY",
    "maintenance": "MAINTENANCE",
}

# ============================================================
# SIGNAL DETECTION (Regex – fallback guaranteed)
# ============================================================
def detect_signals(text: str) -> Dict:
    t = text.lower()
    return {
        "price": bool(re.search(PRICE_REGEX, t)),
        "phone": bool(re.search(PHONE_REGEX, t)),
        "email": bool(re.search(EMAIL_REGEX, t)),
        "link": bool(re.search(LINK_REGEX, t)),
        "abusive": bool(re.search(ABUSIVE_REGEX, t)),
        "owner": bool(re.search(OWNER_REGEX, t)),
    }

# ============================================================
# MOCK LLM ANALYSIS (Pluggable with OpenAI later)
# ============================================================
def llm_analyze(text: str) -> Dict:
    """
    Simulates LLM behavior safely.
    Replace with real LLM later without touching business logic.
    """
    text_l = text.lower()

    # Sentiment
    if any(w in text_l for w in ["great", "excellent", "amazing", "clean"]):
        sentiment = "SENTIMENT_POSITIVE"
    elif any(w in text_l for w in ["bad", "dirty", "worst", "poor", "noisy"]):
        sentiment = "SENTIMENT_NEGATIVE"
    else:
        sentiment = "SENTIMENT_NEUTRAL"

    # Summary
    summary = text[:120] + "..." if len(text) > 120 else text

    # Topic tags
    topics = set()
    for k, v in TOPIC_TAGS.items():
        if k in text_l:
            topics.add(v)

    return {
        "sentiment": sentiment,
        "summary": summary,
        "topics": list(topics),
    }

# ============================================================
# CORE ANALYSIS LOGIC
# ============================================================
def analyze_review(review: Dict) -> Dict:
    text = review["review_text"]

    signals = detect_signals(text)
    llm_out = llm_analyze(text)

    rejection_reasons = []
    special_tags = []
    flags = []

    # ---------- HARD REJECT RULES ----------
    if signals["price"]:
        rejection_reasons.append("PRICE_MENTIONED")
        special_tags.append("PRICE_MENTIONED")

    if signals["phone"] or signals["email"]:
        rejection_reasons.append("CONTACT_INFO_MENTIONED")
        special_tags.append("CONTACT_INFO_MENTIONED")

    if signals["link"]:
        rejection_reasons.append("SPAM_OR_LINK")
        special_tags.append("SPAM_SUSPECT")

    if signals["abusive"]:
        rejection_reasons.append("ABUSIVE_CONTENT")
        special_tags.append("ABUSIVE_CONTENT")

    if signals["owner"]:
        rejection_reasons.append("OWNER_MENTIONED")
        special_tags.append("OWNER_MENTIONED")

    if len(text.strip()) < 20:
        flags.append("TOO_SHORT")

    decision = "REJECT" if rejection_reasons else "PUBLISH"

    tags = list(set(llm_out["topics"] + special_tags))

    return {
        "review_id": review.get("review_id"),
        "hotel_id": review["hotel_id"],
        "rating": review["rating"],
        "review_text": text,
        "publish_decision": decision,
        "rejection_reasons": rejection_reasons,
        "flags": flags,
        "tags": tags,
        "sentiment": llm_out["sentiment"],
        "summary": llm_out["summary"],
        "detected_signals": signals,
        "analyzed_at": datetime.utcnow().isoformat(),
        "model_name": MODEL_NAME,
        "prompt_version": PROMPT_VERSION,
    }

# ============================================================
# FILE READERS
# ============================================================
def read_reviews(path: Path, fmt: str) -> List[Dict]:
    reviews = []

    if fmt == "jsonl":
        with open(path, encoding="utf-8") as f:
            for line in f:
                reviews.append(json.loads(line))

    elif fmt == "json":
        with open(path, encoding="utf-8") as f:
            reviews = json.load(f)

    elif fmt == "csv":
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                r["rating"] = int(r["rating"])
                reviews.append(r)
    else:
        raise HTTPException(400, "Unsupported input format")

    return reviews

# ============================================================
# MYSQL INSERT
# ============================================================
def insert_mysql(rows: List[Dict]):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    q = """
    INSERT INTO reviews_enriched
    (review_id, hotel_id, rating, review_text, publish_decision,
     rejection_reasons, flags, tags, sentiment, summary,
     detected_signals, analyzed_at, model_name, prompt_version)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    data = [
        (
            r["review_id"],
            r["hotel_id"],
            r["rating"],
            r["review_text"],
            r["publish_decision"],
            json.dumps(r["rejection_reasons"]),
            json.dumps(r["flags"]),
            json.dumps(r["tags"]),
            r["sentiment"],
            r["summary"],
            json.dumps(r["detected_signals"]),
            r["analyzed_at"],
            r["model_name"],
            r["prompt_version"],
        )
        for r in rows
    ]

    cur.executemany(q, data)
    conn.commit()
    cur.close()
    conn.close()

# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
def health():
    return {"status": "ok"}

# ---------- Analyze Single Review ----------
@app.post("/reviews/analyze-one")
def analyze_one(payload: Dict):
    payload["hotel_id"] = payload.get("hotel_id", "HOTEL_001")
    return analyze_review(payload)

# ---------- Analyze Bulk Reviews ----------
@app.post("/reviews/analyze-bulk")
def analyze_bulk(hotel_id: str, input_format: str, input_path: str):
    reviews = read_reviews(Path(input_path), input_format)

    results = []
    for r in reviews:
        try:
            r["hotel_id"] = hotel_id
            results.append(analyze_review(r))
        except Exception as e:
            logger.error(f"Failed review {r.get('review_id')}: {e}")

    insert_mysql(results)

    out_path = Path("output/reviews_enriched.csv")
    out_path.parent.mkdir(exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    return {
        "total_processed": len(results),
        "publish_count": sum(1 for r in results if r["publish_decision"] == "PUBLISH"),
        "reject_count": sum(1 for r in results if r["publish_decision"] == "REJECT"),
        "csv_output": str(out_path),
    }

# ---------- Summary Report ----------
@app.get("/reports/summary")
def summary(hotel_id: str):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT COUNT(*) AS total FROM reviews_enriched WHERE hotel_id=%s",
        (hotel_id,),
    )
    total = cur.fetchone()["total"]

    cur.execute(
        """
        SELECT publish_decision, COUNT(*) count
        FROM reviews_enriched
        WHERE hotel_id=%s
        GROUP BY publish_decision
        """,
        (hotel_id,),
    )
    publish_stats = cur.fetchall()

    cur.execute(
        """
        SELECT sentiment, COUNT(*) count
        FROM reviews_enriched
        WHERE hotel_id=%s
        GROUP BY sentiment
        """,
        (hotel_id,),
    )
    sentiment_stats = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "hotel_id": hotel_id,
        "total_reviews": total,
        "publish_stats": publish_stats,
        "sentiment_stats": sentiment_stats,
    }
