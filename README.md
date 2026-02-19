# 🏨 Hotel Review Analysis & Moderation POC

A **FastAPI-based backend Proof of Concept (POC)** for generating, analyzing, moderating, tagging, and storing hotel reviews.
This project simulates a **real-world review moderation pipeline** using rule-based logic and AI-style analysis.

---

## 📌 Project Overview

This system is designed to:

* Generate realistic hotel reviews (including edge and violation cases)
* Analyze reviews for moderation using business rules and AI-style logic
* Decide whether a review should be published or rejected
* Automatically tag reviews with sentiment and topic labels
* Store analyzed results in MySQL
* Support bulk processing and CSV export
* Be fully testable via Swagger (OpenAPI UI)

**Scope:**

* Single hotel (`HOTEL_001`)
* 700+ synthetic reviews
* English + limited Hinglish
* Backend-focused (no UI)

---

## 🛠 Tech Stack

* **Python 3.11**
* **FastAPI** – REST API & Swagger UI
* **MySQL** – Persistent storage
* **Regex + Mock LLM logic** – Review analysis
* **CSV / JSON / JSONL** – Input & output formats
* **Uvicorn** – ASGI server

---

## 📂 Project Structure

```
review-poc/
│
├── main.py                  # FastAPI application
├── generate_reviews.py      # Synthetic review generator
├── requirements.txt
├── README.md
│
├── data/
│   ├── reviews_raw.jsonl    # Generated raw reviews
│   └── reviews_raw.csv
│
├── output/
│   └── reviews_enriched.csv # Processed reviews (bulk)
```

---

## 🔄 System Flow

1. Generate synthetic hotel reviews
2. Analyze reviews (signals, sentiment, tags)
3. Apply moderation rules (publish / reject)
4. Store enriched reviews in MySQL
5. Export processed data to CSV
6. View analytics via API

---

## 🧪 Review Analysis Logic

### Signals Detected

* Price / tariff mention
* Phone number or email
* Links or spam
* Owner / manager mention
* Abusive language

### Moderation Rules

A review is **REJECTED** if it contains:

* Price / tariff information
* Contact details
* Links or spam
* Abusive content
* Owner / manager references

Otherwise, the review is **PUBLISHED**.

---

## 🏷 Tagging System

### Sentiment Tags (exactly one)

* `SENTIMENT_POSITIVE`
* `SENTIMENT_NEUTRAL`
* `SENTIMENT_NEGATIVE`

### Topic Tags (multi-label)

* `CLEANLINESS`
* `ROOM_QUALITY`
* `BATHROOM`
* `FOOD_BREAKFAST`
* `RESTAURANT_FOOD`
* `SERVICE_STAFF`
* `CHECKIN_CHECKOUT`
* `LOCATION`
* `AMENITIES`
* `WIFI`
* `NOISE`
* `PARKING`
* `SAFETY_SECURITY`
* `MAINTENANCE`

### Special Tags

* `PRICE_MENTIONED`
* `CONTACT_INFO_MENTIONED`
* `ABUSIVE_CONTENT`
* `SPAM_SUSPECT`
* `OWNER_MENTIONED`

---

## 🚀 How to Run the Project

### 1️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Setup MySQL

```sql
CREATE DATABASE review_poc;
USE review_poc;

CREATE TABLE reviews_enriched (
    id INT AUTO_INCREMENT PRIMARY KEY,
    review_id VARCHAR(50),
    hotel_id VARCHAR(50),
    rating INT,
    review_text TEXT,
    publish_decision VARCHAR(20),
    rejection_reasons JSON,
    flags JSON,
    tags JSON,
    sentiment VARCHAR(30),
    summary TEXT,
    detected_signals JSON,
    analyzed_at DATETIME,
    model_name VARCHAR(50),
    prompt_version VARCHAR(20)
);
```

### 3️⃣ Generate reviews

```bash
python generate_reviews.py
```

### 4️⃣ Start API server

```bash
uvicorn main:app --reload
```

### 5️⃣ Open Swagger UI

```
http://127.0.0.1:8000/docs
```

---

## 📡 API Endpoints

### Analyze Single Review

`POST /reviews/analyze-one`

```json
{
  "hotel_id": "HOTEL_001",
  "review_text": "Rooms were clean but I paid 6500 per night",
  "rating": 3
}
```

---

### Analyze Bulk Reviews

`POST /reviews/analyze-bulk`

```json
{
  "hotel_id": "HOTEL_001",
  "input_format": "jsonl",
  "input_path": "data/reviews_raw.jsonl"
}
```

---

### Summary Report

`GET /reports/summary?hotel_id=HOTEL_001`

Returns:

* Total reviews
* Publish vs reject counts
* Sentiment distribution

---

## 📤 Output

* **MySQL** → `reviews_enriched` table
* **CSV Export** → `output/reviews_enriched.csv`

Bulk analysis is **append-only** (multiple runs add new rows).

---

## ⚠️ Notes & Limitations

* LLM logic is mocked for POC stability
* Designed for backend demonstration, not production UI
* Regex ensures fallback if AI logic fails
* Append-only DB behavior is intentional for demo purposes

---

## 🎯 Why This Project

This POC demonstrates:

* Backend API design
* Data pipelines & ingestion
* Moderation & policy enforcement
* Scalable bulk processing
* Practical FastAPI + MySQL integration

---

## 👤 Author

**Panav Lodaya**
BBA – International Business
Backend & Data Engineering Enthusiast
