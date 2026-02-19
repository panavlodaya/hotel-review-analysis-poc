import random
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
HOTEL_ID = "HOTEL_001"
TOTAL_REVIEWS = 720  # intentionally > 500

OUTPUT_JSONL = Path("data/reviews_raw.jsonl")
OUTPUT_CSV = Path("data/reviews_raw.csv")

# ============================================================
# DATA POOLS
# ============================================================
REVIEWERS = [
    "Amit", "Rohit", "Sneha", "Pooja", "Rahul",
    "Ankit", "Neha", "Karan", "Simran", "Vikas",
    "Arjun", "Priya", "Nikhil", "Sonal"
]

SOURCES = ["google", "booking", "internal"]

# ---------- BASE TEMPLATES ----------
POSITIVE_REVIEWS = [
    "Great stay, rooms were very clean and staff was polite",
    "Excellent hotel with prime location and good amenities",
    "Amazing service, bathroom was spotless",
    "Loved the breakfast buffet and staff behavior",
    "Very comfortable rooms, will definitely visit again",
    "Gym and pool were well maintained",
]

NEGATIVE_REVIEWS = [
    "Worst stay ever, very dirty rooms",
    "Bad experience, too much noise at night",
    "Poor maintenance and rude staff",
    "Terrible hotel, bathroom smelled bad",
    "Not worth it, rooms were smelly",
    "AC was not working properly",
]

NEUTRAL_REVIEWS = [
    "Hotel was okay, nothing special",
    "Average stay, decent location",
    "Rooms were fine but service was slow",
    "Okay experience, food was average",
    "Stay was acceptable for one night",
]

HINGLISH_REVIEWS = [
    "Room clean tha but staff thoda slow tha",
    "Location achi hai but noise zyada tha",
    "Food theek tha, nothing great",
    "Overall stay okay tha",
]

# ---------- PROBLEMATIC SNIPPETS ----------
PRICE_SNIPPETS = [
    "I paid 6000 per night",
    "Cost was ₹4500",
    "Tariff was 5200 INR",
    "Price is too high for this hotel",
]

PHONE_SNIPPETS = [
    "Call me at 9876543210",
    "My number is 9123456789",
]

EMAIL_SNIPPETS = [
    "Email me at test@gmail.com",
    "Contact: demo@yahoo.com",
]

LINK_SNIPPETS = [
    "Check www.fakehotel.com",
    "More details at http://spamlink.com",
]

OWNER_SNIPPETS = [
    "Owner Mr Sharma was present",
    "Manager Ravi handled the issue",
]

ABUSIVE_SNIPPETS = [
    "This hotel is shit",
    "Worst service, staff is stupid",
]

# ============================================================
# HELPERS
# ============================================================
def random_date():
    days_ago = random.randint(0, 365)
    return (datetime.utcnow() - timedelta(days=days_ago)).isoformat()

def maybe_add(text: str, probability: float, snippets: list) -> str:
    if random.random() < probability:
        return text + ". " + random.choice(snippets)
    return text

# ============================================================
# REVIEW GENERATION
# ============================================================
def generate_review(i: int) -> dict:
    sentiment_type = random.choices(
        ["positive", "neutral", "negative", "hinglish"],
        weights=[0.35, 0.30, 0.25, 0.10],
        k=1
    )[0]

    if sentiment_type == "positive":
        text = random.choice(POSITIVE_REVIEWS)
        rating = random.randint(4, 5)

    elif sentiment_type == "negative":
        text = random.choice(NEGATIVE_REVIEWS)
        rating = random.randint(1, 2)

    elif sentiment_type == "hinglish":
        text = random.choice(HINGLISH_REVIEWS)
        rating = random.randint(2, 4)

    else:
        text = random.choice(NEUTRAL_REVIEWS)
        rating = 3

    # ---------- Inject moderation-breaking content ----------
    text = maybe_add(text, 0.30, PRICE_SNIPPETS)
    text = maybe_add(text, 0.15, PHONE_SNIPPETS)
    text = maybe_add(text, 0.10, EMAIL_SNIPPETS)
    text = maybe_add(text, 0.10, LINK_SNIPPETS)
    text = maybe_add(text, 0.08, OWNER_SNIPPETS)
    text = maybe_add(text, 0.07, ABUSIVE_SNIPPETS)

    return {
        "review_id": f"R{i+1}",
        "hotel_id": HOTEL_ID,
        "reviewer_name": random.choice(REVIEWERS),
        "rating": rating,
        "review_text": text,
        "source": random.choice(SOURCES),
        "created_at": random_date(),
    }

# ============================================================
# MAIN
# ============================================================
def main():
    reviews = [generate_review(i) for i in range(TOTAL_REVIEWS)]

    OUTPUT_JSONL.parent.mkdir(exist_ok=True)
    OUTPUT_CSV.parent.mkdir(exist_ok=True)

    # ---------- JSONL ----------
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for r in reviews:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---------- CSV ----------
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=reviews[0].keys())
        writer.writeheader()
        writer.writerows(reviews)

    print(f"Generated {len(reviews)} reviews")
    print(f"JSONL saved to: {OUTPUT_JSONL}")
    print(f"CSV saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
