# 📰 NewsPulse

## Real-Time News Intelligence & Trend Analytics Platform

NewsPulse is a modern **news intelligence system** that continuously collects live headlines and transforms them into **actionable insights** using NLP, Machine Learning, and AI.

Instead of just listing articles, NewsPulse automatically:

- detects sentiment
- discovers topics
- tracks rising/falling trends
- groups related stories
- summarizes articles with AI

Think:

**Google Trends × News Dashboard × AI Assistant**

---

# 🚀 Features

## 📊 Analytics (Machine Learning)
- Sentiment analysis (positive / neutral / negative)
- Topic modeling (LDA)
- Trend growth detection (24h time window)
- Article clustering
- Similarity search

## 🤖 AI
- Article summarization
- Trend explanations
- Natural language insights

## 📰 Live Data
- Continuous polling from NewsAPI
- Real-time headlines
- Automatic history collection
- No manual datasets

## 🎨 Modern Editorial UI
- Warm “Modern Heritage” design
- Clean typography
- Comfortable reading experience
- Magazine-style layout (not a dashboard)

---

# 🧠 Tech Stack

## Frontend
- React
- Tailwind CSS

## Backend
- FastAPI (Python)

## Data Science / NLP
- scikit-learn
- pandas
- numpy
- spaCy

## AI
- Google Gemini API (summarization)

## Data Source
- NewsAPI

## Storage (for trends)
- SQLite (lightweight time-series cache)

## Hosting
- Frontend → Vercel
- Backend → Render

---

# 🏗 Architecture

```
User
  ↓
React + Tailwind (Vercel)
  ↓ API calls
FastAPI Backend (Render)
  ↓
NewsAPI → live headlines
SQLite → 24h history store
ML models → analytics
Gemini → summaries
```

---

# 📈 How Trends Work (Important)

NewsAPI does not provide historical filtering.

To compute trends, NewsPulse maintains a small internal history.

## Polling
Backend automatically polls:

/v2/top-headlines

every 15–60 minutes.

## Storage
Articles are stored locally in SQLite:

```
backend/news.db
```

Only last 24–48 hours are kept.

## Growth Formula

Window split:
- current → last 12h
- previous → 12–24h

```
growth = (currentCount − previousCount) / previousCount
```

If `previousCount = 0`:
→ marked as **new/emerging**

This enables:
- rising topics
- spikes
- trend detection

Users do NOT need to visit daily.  
The server collects data continuously.

---

# 📰 NewsAPI Usage

## Discovery (default homepage)
Uses:
/v2/top-headlines

For:
- live breaking headlines
- trending analysis

## Search
Uses:
/v2/everything?q=keyword

For:
- keyword/topic analysis

---

# ⚙️ How It Works

## 1. Poll
Backend fetches headlines continuously from NewsAPI.

## 2. Store
Articles saved to SQLite for short-term history.

## 3. Preprocess
- clean text
- tokenize
- lemmatize
- TF-IDF vectorization

## 4. ML Pipeline
- sentiment classification
- topic modeling (LDA)
- trend growth analysis
- similarity clustering

## 5. AI Layer
Gemini generates:
- summaries
- explanations

## 6. Dashboard
Frontend renders:
- trending topics
- sentiment charts
- grouped articles
- summaries

---

# 📁 Project Structure

```
newspulse/
│
├── frontend/        # React + Tailwind UI
├── backend/         # FastAPI + ML + Gemini + SQLite
├── README.md
```

Single monorepo.

Deployment:
- Vercel → /frontend
- Render → /backend

---

# 🔌 API Endpoints (Backend)

### Get trending insights
GET `/trends`

### Search by keyword
GET `/search?q=AI`

### Article summary
POST `/summarize`

---

# 🛠 Local Development

## Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Frontend
```bash
cd frontend
npm install
npm run dev
```

---

# 🔐 Environment Variables

Backend `.env`

```
NEWS_API_KEY=your_newsapi_key
GEMINI_API_KEY=your_gemini_key
```

---

# 🚀 Deployment

## Frontend
Deploy `/frontend` to Vercel

## Backend
Deploy `/backend` to Render

Render persists the SQLite database for trend history.

---

# 🎨 Design System

## Modern Heritage Palette

| Purpose | Color |
|--------|----------------|
| Background | #F7E8D3 (Soft Cream) |
| Secondary | #A47864 (Mocha Mousse) |
| Text | #30364F (Slate Grey) |
| Accent | Cinnamon / Muted Gold |

Style goals:
- warm tones
- premium editorial feel
- readable typography
- generous whitespace

---

# 📌 Future Enhancements
- longer historical trends
- caching
- multilingual support
- alerts & notifications
- user preferences
- database scaling (Postgres if needed)

---

# 📖 Resume Description

Built NewsPulse, a real-time news intelligence platform using React, FastAPI, and scikit-learn that continuously collects live headlines, stores short-term history in SQLite, performs sentiment analysis, topic modeling, and trend detection, and generates AI-powered summaries using Gemini.

---

# 👨‍💻 Author
Sriram