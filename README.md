# NagarAI SOS — Full-stack prototype

A React + Vite dashboard backed by a Python FastAPI service. Includes virtual IoT sensor readings, explainable flood-risk scoring, zone monitoring, alert acknowledgement, risk history, and Citizen SOS reports.

## Requirements
- Python 3.10+
- Node.js 18+

## Run backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
API docs: http://localhost:8000/docs

## Run frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
Open the Vite URL shown in the terminal (normally http://localhost:5173).

## Connect a deployed backend
Create `frontend/.env`:
```env
VITE_API_URL=https://your-api-domain.example
```
Restart Vite after changing environment variables.

## Included API routes
- `GET /api/dashboard`
- `GET /api/readings`
- `GET /api/history`
- `GET /api/alerts`
- `POST /api/alerts/{id}/acknowledge`
- `POST /api/simulate` with `normal`, `heavy_rain`, `rising_water`, or `reset`
- `POST /api/sos`
- `GET /api/sos`
- `GET /api/health`

## Important prototype notes
- Sensor data is simulated by the backend. It is not connected to physical sensors or a live municipal feed.
- Data is held in memory and resets when the backend restarts. Supabase persistence, authentication, role permissions, SMS integration, real geolocation, and production security have not been configured.
- The risk score is an explainable demonstration formula (40% water level, 35% rainfall, 25% rise rate), not a validated public-safety prediction model. Calibrate and independently validate it before real-world use.
- CORS is permissive for local development. Restrict allowed origins before deployment.
