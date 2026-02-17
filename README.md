# RedPajama Chat App

Full-stack chat and investigation workspace with:

- **Frontend**: Vue 3 + Vite + PrimeVue
- **API**: FastAPI + PostgreSQL (pgvector)
- **AI integrations**: Ollama (frontend chat), OpenAI/Anthropic hooks (backend)

## Project Structure

- `frontend/` - Vue application (chat, investigations, collections, audit pages)
- `api/` - FastAPI backend (documents, audit metrics, health/version)

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker (for local PostgreSQL + pgvector)

## Quick Start

### 1) Start database

```bash
docker compose -f api/docker-compose.yml up -d
```

### 2) Configure backend

```bash
cp api/.env.example api/.env
```

Set at least these values in `api/.env`:

- `DATABASE_URL`
- `SECRET_KEY`

### 3) Install and run backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

- API root: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- Swagger docs: `http://localhost:8000/docs`

### 4) Configure frontend

```bash
cp frontend/.env.example frontend/.env
```

If needed, update `VITE_OLLAMA_ENDPOINT` in `frontend/.env`.

### 5) Install and run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- App: `http://localhost:5173`

## Useful Commands

From `frontend/`:

```bash
npm run dev
npm run build
npm run preview
```

From repo root (backend):

```bash
uvicorn api.main:app --reload
pytest api/tests
```

## Notes

- Audit endpoints currently return seeded/dummy analytics data.
- Document upload/search endpoints are available under `/documents`.
