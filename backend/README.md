# Social Search Backend  Find Like-minded People by YouTube Interests

Core backend for finding people with similar interests based on YouTube watch history analysis.

## Architecture

- **FastAPI**  Web framework
- **SQLAlchemy** — ORM, SQLite
- **Google OAuth**  Authentication and YouTube access
- **Hybrid recommendation system**  TF-IDF + cosine similarity (content-based + behavioral)

## Quick Start

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Fill in GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Compose (SQLite + API + web)

From the **repository root**:

```bash
cp backend/.env.example backend/.env
# Set SECRET_KEY and other secrets in backend/.env

docker compose up -d --build
```

Compose sets `DATABASE_URL` to SQLite at `/app/data/social_search.db` inside the backend container. Data persists in the **`backend_data`** volume. Uploaded avatars persist in **`backend_uploads`**.

- **backend**: http://localhost:8000 — `alembic upgrade head` runs on container start (`docker-entrypoint.sh`).
- **frontend**: http://localhost (port **80**) — nginx proxies `/api` to the backend.

Health check: `GET http://localhost:8000/health`

For local development without Docker, keep `DATABASE_URL=sqlite:///./social_search.db` in `backend/.env` and run `uvicorn` as in Quick Start.

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/google` | URL for Google OAuth |
| POST | `/api/auth/google/callback` | Exchange code for tokens |
| GET | `/api/auth/me` | Current user |
| POST | `/api/youtube/sync` | Sync YouTube history |
| GET | `/api/recommendations/similar-users` | Similar users (like-minded) |
| POST | `/api/data/import-kaggle` | Import CSV from Kaggle for profile |

## Environment Variables (.env)

```env
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback  # or your frontend URL
DATABASE_URL=sqlite:///./social_search.db
SEMANTIC_MODEL_NAME=all-MiniLM-L6-v2
```

## A/B Semantic Model Benchmark

Compare two semantic backbones on ranking quality and speed while keeping **hybrid** as production baseline:

```bash
cd backend
$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe -m scripts.ab_compare_semantic_models
```

Default comparison:
- `all-MiniLM-L6-v2` (faster)
- `all-mpnet-base-v2` (usually higher quality, slower)

Custom models:

```bash
cd backend
$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe -m scripts.ab_compare_semantic_models --models all-MiniLM-L6-v2 paraphrase-multilingual-MiniLM-L12-v2
```

## Kaggle Dataset

For model training and profile enrichment:

1. Download a dataset (e.g. [YouTube Video Metadata](https://www.kaggle.com/datasets/gpreda/kaggle-youtube-video-metadata))
2. After authentication: POST `/api/data/import-kaggle` with CSV file
3. Expected columns: `video_id`, `title`, `channel_id`, `channel_title`, `category_id`, `tags`, `description`

## Project Structure

```
app/
├── api/          # Routes (auth, users, youtube, recommendations, data)
├── core/         # Config, database
├── models/       # SQLAlchemy (User, WatchHistory, VideoMetadata, UserProfile)
├── schemas/      # Pydantic
├── services/
│   ├── auth.py       # Google OAuth
│   ├── youtube.py    # YouTube API
│   ├── recommendation.py
│   ├── data_enricher.py
│   └── ml/           # HybridRecommender, ProfileBuilder, SimilarityEngine
└── main.py
```
