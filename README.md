# 🏗️ AI-Powered Multimodal Construction Intelligence Platform

A full-stack decision-support system for construction professionals. It analyses **text, images and structured project data** with a multimodal LLM and returns strictly validated JSON that a React dashboard renders.

**Demo:** _add your deployed link here_ · **Repo:** _add your GitHub link here_

## Features
| Module | Input | Output |
|---|---|---|
| 🦺 Site Safety | site photo + notes | safety score, risk level, PPE summary, violations with fixes |
| 🧱 Crack Detection | wall/slab photo | crack type, severity, causes, actions, urgency |
| 🏠 Real Estate Valuation | location, area, age, condition | value range, price/sq ft, factors, assumptions |
| 📐 Project Planning | project type, area, floors | phases, durations, materials, risks, critical path, cost range |
| 🧑‍🔧 Daily Site Assistant | free text (+ photo) | answer, priority, action items |
| 🌦️ Weather Advisory | city + activity | live forecast (Open-Meteo) → work suitability & precautions |
| 📚 Knowledge Assistant | question | answer, key points, standards referenced |

## Architecture
```
React (Vite)  ──multipart/form-data──►  FastAPI  ──►  Multimodal LLM (Claude)
   ▲                                       │  prompts.py  (role prompts per module)
   └────────── validated JSON ◄────────────┘  schemas.py  (Pydantic contracts)
                                           └► Open-Meteo (weather)
```
* **Strict JSON contracts:** every endpoint has a Pydantic `response_model`; the LLM output is parsed, validated and retried once if malformed, so the frontend never receives unexpected shapes.
* **Declarative frontend:** `frontend/src/features.js` describes each module's form; one generic renderer displays any report.

## Project structure
```
backend/   FastAPI app (app/main.py, llm.py, schemas.py, prompts.py) + tests
frontend/  React + Vite dashboard
```

## Run locally

### Option 1: Streamlit Dashboard (All-in-One)
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
> Enter your `ANTHROPIC_API_KEY` in the sidebar or save it in `.streamlit/secrets.toml`.

### Option 2: Full-Stack (FastAPI + React)
**Backend** (Python 3.10+)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # put your ANTHROPIC_API_KEY in .env
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

**Frontend** (Node 18+)
```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

**Tests:** `cd backend && python -m pytest -q` (LLM is mocked; no key needed)

## API
All endpoints are `POST /api/<module>` with `multipart/form-data`: `safety`, `cracks`, `valuation`, `planning`, `assistant`, `weather`, `knowledge`. `GET /api/health` reports status.

## Deployment Options

### 🚀 1. Deploy on Streamlit Community Cloud (Recommended & Free)
1. Fork or push this repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io).
3. Click **New app** and select:
   - **Repository:** `vishaljain-code/Multimodal-Construction-Intelligence-Platform`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. Expand **Advanced settings** -> **Secrets** and enter:
   ```toml
   ANTHROPIC_API_KEY = "your-anthropic-api-key"
   ```
5. Click **Deploy!** Your app will be live with a shareable URL.

### 🌐 2. Full-Stack Deployment (Render + Vercel)
* **Backend → Render / Railway:** root dir `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set env vars `ANTHROPIC_API_KEY` and `CORS_ORIGINS=https://<your-frontend-url>`. (A `Dockerfile` is included; also works on AWS App Runner / Elastic Beanstalk.)
* **Frontend → Vercel / Netlify:** root dir `frontend`, build `npm run build`, output `dist`. Set `VITE_API_URL=https://<your-backend-url>`.

## Disclaimer
Outputs are AI-generated aids. Crack, safety and valuation results must be verified by a licensed engineer / certified appraiser.
