# Voice2Store AI

Voice2Store AI is an AI-powered voice-to-website SaaS platform for small retail businesses.

## Stack

- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: Python FastAPI
- API connectivity: `NEXT_PUBLIC_API_URL` → FastAPI backend

## Project structure

- `frontend/` - Next.js app and dashboard UI
- `backend/` - FastAPI API backend
- `docker-compose.yml` - local containerized stack for frontend, backend, and Postgres
- `.env.example` - frontend and shared environment variables
- `backend/.env.example` - backend production environment template

## Quick start

### Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production containers

```bash
docker compose build
docker compose up -d
```

Open http://localhost:3000 for the frontend and http://localhost:8000/docs for the FastAPI docs.

## Production deployment

See [docs/aws-production-deployment.md](docs/aws-production-deployment.md) for AWS ECS/RDS deployment guidance, security hardening, and environment setup.
