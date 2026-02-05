# 🚀 NewsPulse - Deployment Guide

Complete guide for deploying NewsPulse to production: Backend on Render, Frontend on Vercel.

---

## 📋 Prerequisites

- GitHub account
- [Render account](https://render.com) (free)
- [Vercel account](https://vercel.com) (free)
- NewsAPI key from [newsapi.org](https://newsapi.org)
- Google Gemini API key from [ai.google.dev](https://ai.google.dev)

---

## 🔧 Backend Deployment (Render)

### 1. Push to GitHub
spaCy 3.8.11 + en_core_web_sm
scikit-learn 1.6.1
NewsAPI (HTTP client)
Google Gemini API (gemini-1.5-flash)
```

### Frontend
```
React 18.3.1
Vite 5.4.21
Tailwind CSS 3.4.13
```

---

## 📊 Configuration

### Polling Settings (backend/.env)
```env
NEWS_API_KEY=your_newsapi_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Default Parameters
- **Poll Scope**: country=us, language=en
- **Poll Interval**: 30 minutes
- **Retention Period**: 48 hours
- **Trend Window**: 24 hours (split into two 12h windows for comparison)
- **Database**: SQLite at `backend/news.db`

---

## � Backend Deployment (Render)

### 1. Push to GitHub

```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `newspulse-api` (or your choice)
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python -m spacy download en_core_web_sm
     ```
   - **Start Command**: 
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

### 3. Add Environment Variables

In Render dashboard, go to **Environment** tab and add:

| Key | Value |
|-----|-------|
| `NEWS_API_KEY` | Your NewsAPI key |
| `GEMINI_API_KEY` | Your Gemini API key |
| `POLL_INTERVAL_MINUTES` | `30` |
| `RETENTION_HOURS` | `48` |
| `PYTHON_VERSION` | `3.11.0` |

### 4. Deploy

Click **Create Web Service** - Render will build and deploy automatically.

**Your backend URL**: `https://newspulse-api.onrender.com` (or your chosen name)

> ⚠️ **Note**: Free Render services spin down after 15 minutes of inactivity. First request after idle may take 30-60 seconds.

---

## 🎨 Frontend Deployment (Vercel)

### 1. Create Environment File

In `frontend/` directory, create `.env.production`:

```env
VITE_API_BASE_URL=https://your-backend-url.onrender.com
```

Replace `your-backend-url` with your actual Render URL from above.

### 2. Commit Environment Config

```bash
git add frontend/.env.production
git commit -m "Add production environment config"
git push origin main
```

### 3. Deploy to Vercel

**Option A: Via Vercel Dashboard**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)

**Option B: Via CLI**
```bash
cd frontend
npx vercel --prod
```

### 4. Add Environment Variable

In Vercel project settings:
1. Go to **Settings** → **Environment Variables**
2. Add:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://your-backend-url.onrender.com`
   - **Environments**: Production, Preview

### 5. Redeploy

Vercel will automatically deploy. Your site will be live at:
- `https://your-project-name.vercel.app`

---

## ✅ Verification Checklist

### Backend Health Check
```bash
curl https://your-backend-url.onrender.com/health
```
Expected: `{"status":"ok"}`

### Frontend Connection Test
1. Visit your Vercel URL
2. Open browser DevTools → Network tab
3. Search for something
4. Verify API requests go to your Render backend URL

### Feature Timeline
- ✅ **Immediate**: Latest News, Search, Related Stories
- ⏱️ **~2 hours**: Breaking News detection
- ⏱️ **~12-24 hours**: Trending analysis

---

## 🔒 Security Notes

### Production CORS (Optional)

For stricter security, update `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-project-name.vercel.app",
        "http://localhost:5173",  # Local development
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🐛 Troubleshooting

### Backend Issues

**"Application failed to respond"**
- Check Render logs: Dashboard → Your Service → Logs
- Verify all environment variables are set
- Ensure spaCy model downloaded (check build logs)

**"Database locked" errors**
- Normal on Render free tier with limited disk I/O
- Consider upgrading to paid plan for production use

### Frontend Issues

**API calls failing**
- Verify `VITE_API_BASE_URL` matches your Render URL exactly
- Check CORS settings in backend
- Look for errors in browser console

**Environment variables not working**
- Redeploy after adding variables: Vercel → Deployments → Redeploy
- Verify variable name has `VITE_` prefix

---

## 🔄 Updates & Redeployment

### Backend Updates
```bash
git add backend/
git commit -m "Update backend"
git push origin main
```
Render auto-deploys on push.

### Frontend Updates
```bash
git add frontend/
git commit -m "Update frontend"
git push origin main
```
Vercel auto-deploys on push.

---

## 💰 Cost Breakdown

| Service | Plan | Cost | Features |
|---------|------|------|----------|
| Render | Free | $0/month | 750 hours/month, sleeps after 15min idle |
| Vercel | Hobby | $0/month | 100GB bandwidth, unlimited deployments |
| NewsAPI | Developer | $0/month | 100 requests/day |
| Gemini | Free | $0/month | 15 requests/minute |

**Total**: $0/month for testing/portfolio use

---

## 📈 Scaling to Paid (Future)

When you need 24/7 uptime and higher limits:

- **Render**: Upgrade to Starter ($7/month) for no sleep + persistent disk
- **NewsAPI**: Business plan ($449/month) for production use
- **Gemini**: Pay-as-you-go for higher quotas
- **Vercel**: Pro ($20/month) for more bandwidth

---

## 🎉 You're Done!

Your app is now live:
- **Frontend**: `https://your-project.vercel.app`
- **Backend**: `https://newspulse-api.onrender.com`

Share the Vercel link for your portfolio! 🚀

---

## 📚 Local Development Reference

### Start Backend
```powershell
cd c:\Projects\NewsPulse\backend
python -m uvicorn app.main:app --reload
```
Backend available at: http://127.0.0.1:8000

### Start Frontend
```powershell
cd c:\Projects\NewsPulse\frontend
npm run dev
```
Frontend available at: http://localhost:5173/

**Status**: ✅ 3/3 tests passing (ranking logic validated)

### Manual API Testing
```powershell
# Test trends endpoint
Invoke-WebRequest -Uri http://127.0.0.1:8000/trends -UseBasicParsing

# Test search endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8000/search?q=technology&sortBy=publishedAt" -UseBasicParsing

# Test summarize endpoint
$body = '{"url": "https://example.com/article"}' 
Invoke-WebRequest -Uri http://127.0.0.1:8000/summarize -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

---

## 🔍 Database Inspection

### Check Article Count
```powershell
cd c:\Projects\NewsPulse\backend
C:/Users/srira/AppData/Local/Programs/Python/Python313/python.exe -c "import sqlite3; conn = sqlite3.connect('news.db'); cur = conn.cursor(); count = cur.execute('SELECT COUNT(*) FROM articles').fetchone()[0]; print(f'Articles: {count}'); conn.close()"
```

### View Latest Articles
```powershell
C:/Users/srira/AppData/Local/Programs/Python/Python313/python.exe -c "import sqlite3; conn = sqlite3.connect('news.db'); cur = conn.cursor(); rows = cur.execute('SELECT title, published_at FROM articles ORDER BY published_at DESC LIMIT 5').fetchall(); print('\n'.join([f'{r[1]}: {r[0][:60]}...' for r in rows])); conn.close()"
```

---

## 🐛 Troubleshooting

### Issue: ValidationError on startup
**Cause**: .env file was empty or not being loaded
**Solution**: 
1. Ensured .env file has actual content (not 0 bytes)
2. Updated config.py to use absolute path for env_file:
```python
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"
model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")
```

### Issue: spaCy model not found
**Cause**: en_core_web_sm not downloaded
**Solution**: 
```powershell
python -m spacy download en_core_web_sm
```

### Issue: Empty trending list
**Cause**: Not enough data collected yet (requires 24h of data for meaningful trends)
**Solution**: Wait for poller to run multiple cycles. After several hours, trends will appear.

---

## 📝 Next Steps / Future Enhancements

### Short Term
- [ ] Wire sentiment analysis into `/search` endpoint response
- [ ] Add clustering/topic modeling to `/search` results
- [ ] Implement frontend search UI component
- [ ] Add article summarization UI component

### Medium Term
- [ ] Add filtering by category/source
- [ ] Implement user preferences (saved searches, custom alerts)
- [ ] Add data visualization (trend charts, sentiment graphs)
- [ ] Deploy to Render.com with persistent disk for SQLite

### Long Term
- [ ] Multi-language support
- [ ] Advanced NLP features (entity extraction, relationship mapping)
- [ ] Real-time WebSocket updates for live trends
- [ ] Machine learning model for predicting viral topics

---

## 📦 Deployment to Render.com

### Backend (Web Service)
```yaml
# render.yaml
services:
  - type: web
    name: newspulse-api
    runtime: python
    buildCommand: "pip install -r requirements.txt && python -m spacy download en_core_web_sm"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: NEWS_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
    disk:
      name: newspulse-data
      mountPath: /app/data
      sizeGB: 1
```

**Important**: Update `sqlite_path` in Settings to `/app/data/news.db` for persistent storage.

### Frontend (Static Site)
```yaml
  - type: web
    name: newspulse-frontend
    runtime: static
    buildCommand: "npm install && npm run build"
    staticPublishPath: dist
    envVars:
      - key: VITE_API_BASE_URL
        value: https://newspulse-api.onrender.com
```

---

## 👨‍💻 Development Notes

### Code Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI app + poller lifecycle
│   ├── core/config.py       # Pydantic Settings (reads .env)
│   ├── services/
│   │   ├── poller.py        # Background headline poller
│   │   ├── db.py            # SQLite operations
│   │   ├── newsapi_client.py
│   │   ├── gemini_client.py
│   │   ├── sentiment.py     # Pre-trained sentiment model
│   │   └── analytics/
│   │       ├── keywords.py  # spaCy keyword extraction
│   │       └── trends.py    # Trend ranking logic
│   └── api/routes/
│       ├── trends.py        # GET /trends
│       ├── search.py        # GET /search
│       └── summarize.py     # POST /summarize
├── models/
│   ├── vectorizer.pkl       # TfidfVectorizer for sentiment
│   └── sentiment.pkl        # LogisticRegression classifier
├── tests/
│   └── test_trends.py       # Pytest for ranking logic
└── scripts/
    └── train_sentiment.py   # Generates .pkl artifacts

frontend/
├── src/
│   ├── App.jsx              # Main React component
│   └── index.css            # Tailwind + Modern Heritage theme
└── package.json
```

### Key Design Decisions
1. **SQLite over PostgreSQL**: Simpler deployment, adequate for 48h rolling window
2. **Polling over Streaming**: NewsAPI doesn't support WebSockets; 30min cadence is sufficient
3. **spaCy over NLTK**: Better accuracy for noun chunk extraction
4. **Pre-trained Sentiment**: Avoids runtime training cost, sufficient for v1
5. **Locked Ranking Algorithm**: Business requirement to prioritize emerging over growth

---

## 🎯 Success Metrics

- ✅ Backend starts without errors
- ✅ Poller collects headlines every 30 minutes
- ✅ SQLite stores articles with timestamps
- ✅ `/trends` endpoint returns valid JSON
- ✅ Frontend displays trending keywords
- ✅ Pytest tests validate ranking logic
- ✅ All dependencies install cleanly on Python 3.13

---

**System deployed successfully on**: February 4, 2026
**Total development time**: ~2 hours
**Lines of code**: ~1,200 (backend + frontend + tests)
