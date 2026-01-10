# Backend (Flask)

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python backend/app.py
```

Serves `GET /api/hello` on `http://localhost:5000`.

## Environment Variables

- Create `backend/.env` (use `backend/.env.example` as a template).
- Variables are loaded automatically at app startup via `python-dotenv`.
- `GET /api/hello` returns `hasKey: true/false` to confirm `.env` was loaded (does not expose values).
