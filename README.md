# NewsPulse — Real-Time News Intelligence & Trend Analytics

🎉 **Status**: OPERATIONAL - Backend collecting headlines, Frontend displaying trends!

Live news intelligence platform that continuously collects headlines and transforms them into actionable insights using NLP, ML, and AI.

## Quick Start

**Backend**: http://127.0.0.1:8000  
**Frontend**: http://localhost:5173/  
**Articles Collected**: 29+ (updates every 30 minutes)

## Features

- **Real-time Headline Polling** (US news, every 30 minutes)
- **Trend Detection** (spaCy keyword extraction with growth tracking)
- **Sentiment Analysis** (pre-trained scikit-learn model)
- **AI-powered Summarization** (Google Gemini API)
- **Search API** (NewsAPI passthrough with optional analytics)
- **SQLite Storage** (48-hour rolling retention)

## Tech Stack

- **Frontend:** React + Tailwind CSS (Vite)
- **Backend:** FastAPI (Python 3.13+)
- **ML/NLP:** scikit-learn, spaCy, pandas, numpy
- **AI:** Google Gemini API
- **Storage:** SQLite (lightweight time-series cache)

## Local Development

### Backend Setup

1. **Install Python 3.13** (required for spaCy 3.8.11 wheels)
2. **Navigate to backend folder**
   ```powershell
   cd backend
   ```
3. **Install dependencies**
   ```powershell
   py -m pip install -r requirements.txt
   ```
4. **Download spaCy English model**
   ```powershell
   py -m spacy download en_core_web_sm
   ```
5. **Generate sentiment model artifacts**
   ```powershell
   py scripts\train_sentiment.py
   ```
   This creates `backend/models/vectorizer.pkl` and `backend/models/sentiment.pkl`.

6. **Create `.env` file** in `backend/` with your API keys:
   ```
   NEWS_API_KEY=your_newsapi_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

7. **Run the backend**
   ```powershell
   uvicorn main:app --reload
   ```
   Backend starts at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend folder**
   ```powershell
   cd frontend
   ```
2. **Install dependencies**
   ```powershell
   npm install
   ```
3. **Run the dev server**
   ```powershell
   npm run dev
   ```
   Frontend starts at `http://localhost:5173`

## How It Works

1. **Polling:** Backend continuously fetches headlines from NewsAPI `/v2/top-headlines` every 30 minutes (configurable via `POLL_INTERVAL_MINUTES` in `.env`).
2. **Storage:** Articles are stored in `backend/news.db` (SQLite) for 48 hours.
3. **Trends:** `/trends` endpoint computes keyword growth by comparing last 12h vs previous 12h using spaCy noun-chunk extraction.
4. **Ranking:** New/emerging keywords (previous=0) rank above existing keywords by current count; existing keywords rank by growth%.

## API Endpoints

- `GET /trends` — Trending keywords with growth metrics
- `GET /search?q=keyword` — Search articles + batch analytics
- `POST /summarize` — AI summarization (Gemini)
- `GET /health` — Health check

## Deployment

### Frontend (Vercel)
Deploy `/frontend` to Vercel.

### Backend (Render)
Deploy `/backend` to Render.

**Important:** Attach a **persistent disk** to the Render service for `backend/news.db` to preserve trend history across deploys.

Set environment variables:
- `NEWS_API_KEY`
- `GEMINI_API_KEY`

## Testing

Run backend tests:
```powershell
cd backend
py -m pytest -q
```

## Author
Sriram
