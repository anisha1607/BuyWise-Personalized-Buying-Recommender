# BuyWise

**Turn scattered product reviews into a personalized buying decision.**

Product reviews are everywhere — Amazon, YouTube, BestBuy — but reading across all of them to make one buying decision is slow and overwhelming. BuyWise scrapes, cleans, and structures that unstructured text into a single dashboard: a fit score, aspect-level sentiment breakdown, source comparison, contradictions, and a plain-English verdict tailored to your budget and use case.

---

## The Core Problem: Unstructured → Structured

Raw review text is messy. A single review might say:

> *"Sound is incredible but it killed my ears after 2 hours and the ANC is a bit overhyped for the price."*

BuyWise breaks this into structured signals:

| Field | Value |
|---|---|
| `aspect` | sound, comfort, performance, price |
| `sentiment` | +0.72, −0.41, −0.18, −0.29 |
| `source` | Amazon |
| `rating` | 4.0 |

Aggregated across hundreds of reviews and weighted by your personal priorities, this becomes a **Fit Score** — a single 0–100 number that answers *"should I buy this, for my use case, at my budget?"*

---

## Data Pipeline

```
Multi-source ingestion
  ├── Amazon         (web scraper: search → ASIN → review page)
  ├── BestBuy        (web scraper: search → SKU → UGC reviews API)
  ├── YouTube        (transcript API → video description fallback)
  ├── Trustpilot     (web scraper: brand page → paginated review cards)
  ├── Kaggle / CSV   (auto-scan backend/data/ for any .csv / .json / .jsonl)
  └── Paste          (user-supplied raw text, split by paragraph)
          │
          ▼
   Cleaning Agent
   • deduplicate by MD5 hash
   • filter < 8 words or > 800 words
   • normalize source labels, ratings, dates
          │
          ▼
   Aspect Agent  (VADER sentiment per sentence × keyword buckets)
   • 8 aspects: comfort, price, battery, sound,
                durability, performance, design, connectivity
          │
          ▼
   Personalization Agent
   • user weights = base priority × use-case boost × budget floor
   • weighted average sentiment → raw score [0, 100]
   • deal-breaker penalty: −8 pts per triggered aspect
          │
          ▼
   LLM Layer  (Groq — Llama 3)
   • verdict + hypothesis          (explanation_agent)
   • personalized fit analysis     (analyze route)
   • devil's-advocate critical take (critical_agent)
          │
          ▼
   Structured Dashboard
   • Fit Score  • Aspect Chart  • Source Comparison
   • Contradiction Detector  • Pros / Cons  • Evidence Cards
   • Preference vs. Reality  • Export JSON / CSV
```

---

## Key Design Decisions & Trade-offs

**VADER over a transformer model for sentiment**
VADER runs in microseconds per sentence and needs no GPU. A fine-tuned review model (e.g., RoBERTa-sentiment) would score more accurately on edge cases but adds ~400 MB of model weight and seconds of latency per request. For a live web app the speed win matters more.

**Keyword-based aspect extraction over NER/dependency parsing**
Matching sentences against curated keyword lists is deterministic and fast. A proper NLP approach (spaCy dependency parsing, or an LLM for entity-aspect extraction) would handle paraphrases better ("the cups squeeze my head" → comfort) but is significantly slower and harder to tune. The current lexicon catches ~90% of mentions in practice.

**Per-source scraping with concurrent execution**
Amazon, BestBuy, and YouTube run in a `ThreadPoolExecutor(max_workers=3)` so all three fire simultaneously. This cuts collection time from ~35 seconds (sequential) to ~10 seconds (bottlenecked by the slowest source). The FastAPI endpoint is a plain `def` (not `async def`) so scrapers run in FastAPI's thread pool rather than blocking uvicorn's event loop.

**LLM used only for synthesis, not for core scoring**
The fit score and aspect sentiments are computed deterministically from real review data. The LLM is brought in only at the end to write the human-readable verdict and critical take — so the numbers are trustworthy even if the API is slow or unavailable (graceful fallback text is returned).

**Flexible file ingestion over a fixed schema**
`load_file_reviews()` auto-scans `backend/data/` for `.csv`, `.json`, and `.jsonl` files and uses priority-ordered column name matching to handle Yelp (`stars`, `text`), UCSD Amazon 2023 (`rating`, `reviewText`, `asin`), and custom exports. Drop any new dataset file in the folder and it gets picked up automatically.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| NLP / Sentiment | VADER (`vaderSentiment`) |
| LLM | Groq API (Llama 3.3 70B / 3.1 8B) |
| Scraping | `requests`, `BeautifulSoup4`, `lxml`, `httpx` |
| YouTube | `youtube-transcript-api` |
| Data | `pandas` |
| Frontend | Next.js 14 (App Router), TypeScript |
| Charts | Recharts |

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free [Groq API key](https://console.groq.com/)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
GROQ_API_KEY=your_key_here
```

Start the API:
```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. Optional: seed local review data

```bash
cd backend
python generate_sample_data.py
```

This creates `backend/data/amazon_reviews.csv` and `backend/data/bestbuy_reviews.csv` with sample reviews for the demo products.

---

## Adding Your Own Data

Drop any of the following into `backend/data/` and it will be picked up automatically:

| Format | Expected columns |
|---|---|
| Standard CSV | `product`, `rating`, `text`, `date`, `source` |
| Yelp dataset | `text`, `stars`, `date` |
| UCSD Amazon 2023 JSONL | `text` / `reviewText`, `rating`, `timestamp`, `asin` |
| Any CSV | flexible matching on common column names |

---

## Project Structure

```
BuyWise/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── data/                        # drop CSV / JSONL datasets here
│   ├── agents/
│   │   ├── data_collection_agent.py # scraping + ingestion
│   │   ├── cleaning_agent.py        # dedup + normalization
│   │   ├── aspect_agent.py          # VADER sentiment × aspects
│   │   ├── personalization_agent.py # weighted fit score
│   │   ├── explanation_agent.py     # LLM verdict
│   │   ├── critical_agent.py        # LLM devil's advocate
│   │   ├── eda_agent.py             # source comparison + contradictions
│   │   └── preference_agent.py      # user weight computation
│   └── routers/
│       ├── analyze.py               # POST /api/analyze
│       └── export.py                # POST /api/export
└── frontend/
    └── src/
        ├── app/page.tsx             # 4-step wizard (search → prefs → loading → dashboard)
        ├── components/
        │   ├── FitScore.tsx
        │   ├── AspectChart.tsx
        │   ├── SourceComparison.tsx
        │   ├── PreferenceVsReality.tsx
        │   └── ResultCards.tsx
        └── lib/api.ts               # typed API client
```
