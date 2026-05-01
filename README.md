# BuyWise - Personalized Buying Recommender

BuyWise is an advanced, AI-driven product analysis platform designed to help users make better purchasing decisions. By aggregating and analyzing reviews from multiple sources (Amazon, YouTube, and BestBuy), BuyWise provides a personalized "Fit Score" and deep insights tailored to your specific needs, budget, and priorities.

![BuyWise Banner](https://images.unsplash.com/photo-1557821552-17105176677c?q=80&w=1600&auto=format&fit=crop)

## 🚀 Key Features

- **Personalized Recommendations**: Input your budget, use case, and priorities (e.g., comfort, performance, durability) to get a tailored analysis.
- **Multi-Source Scraper**: Automatically pulls data from Amazon reviews, YouTube transcripts, and BestBuy listings.
- **Multi-Agent AI System**:
  - **Data Collection Agent**: Orchestrates scrapers for live product data.
  - **Critical Agent**: Provides a "skeptical" expert view, highlighting trade-offs that others might miss.
  - **Preference Agent**: Maps user needs to technical product aspects.
  - **EDA & Aspect Agents**: Perform sentiment analysis and technical breakdown of features.
- **Evidence-Based Verdicts**: Every claim is backed by real snippets from the web, complete with source links.
- **Interactive AI Chat**: Ask specific questions about a product (e.g., "Is this good for long commutes?") and get answers based on analyzed reviews.
- **Market Intelligence**: View competitor comparisons, price value badges, and sentiment trends.

## 🛠️ Technology Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **AI Models**: [Groq](https://groq.com/) (Llama 3.1) for primary analysis, [HuggingFace](https://huggingface.co/) for fallback.
- **Data Processing**: Pandas, NumPy, VADER Sentiment Analysis.
- **NLP**: Sentence Transformers for semantic search and relevance.
- **Scraping**: BeautifulSoup4, HTTPX, YouTube Transcript API.

### Frontend
- **Framework**: [Next.js 14](https://nextjs.org/) (React)
- **Language**: TypeScript
- **Styling**: Tailwind CSS for a premium, responsive UI.
- **Visualization**: [Recharts](https://recharts.org/) for sentiment and aspect distribution.

## 📦 Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- [Groq API Key](https://console.groq.com/)

### 1. Clone the Repository
```bash
git clone https://github.com/anisha1607/BuyWise-Personalized-Buying-Recommender.git
cd BuyWise-Personalized-Buying-Recommender
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/scripts/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory (or use the one in the root):
```env
GROQ_API_KEY=your_key_here
HF_TOKEN=your_optional_hf_token_here
```

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🏗️ Architecture

BuyWise uses a modular **Multi-Agent Orchestration** pattern:

1. **User Interface**: Collects preferences and product search terms.
2. **Preference Agent**: Translates "everyday use" into specific weights for aspects like "comfort" or "battery".
3. **Data Pipeline**: Scrapers fetch raw HTML/Transcripts; the **Cleaning Agent** sanitizes them.
4. **Analysis Engine**:
   - **LLM Service**: Summarizes data into JSON format.
   - **Sentiment Engine**: Assigns scores to specific product features.
5. **Synthesis**: The **Critical Agent** adds a final layer of expert nuance before presenting the dashboard.

### ⚖️ Architectural Tradeoffs

| Choice | Pro | Con |
| :--- | :--- | :--- |
| **Multi-Agent Orchestration** | Superior reasoning and modularity; agents can be refined independently. | Increased latency due to sequential LLM calls and complex state management. |
| **Hybrid LLM Strategy** | High performance with Groq (Llama 3) and high reliability with HF fallbacks. | Requires managing multiple API keys and handling diverse response schemas. |
| **Live Scraping** | Access to fresh, raw data (YouTube transcripts, Amazon reviews) without API costs. | Fragile to UI changes; requires constant maintenance of scrapers. |
| **Client-Side API Proxy** | Simplified frontend logic and avoidance of CORS issues during development. | Adds a small layer of overhead; requires a running backend server for all requests. |

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
*Built for the intersection of AI and Commerce.*
