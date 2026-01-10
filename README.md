# Monorepo: React + Flask (Minimal)

- Backend: Flask at `/api/hello`
- Frontend: React + Vite with dev proxy to backend

## Quickstart (Windows PowerShell)

### Backend
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python backend/app.py
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — it will call `http://localhost:5000/api/hello`.
