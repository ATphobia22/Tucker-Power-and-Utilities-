# PTDT v33 — Windows Desktop (.exe) Build

Electron + Python sidecar packaging for standalone Windows installers.

## Prerequisites (Windows)

- Python 3.11+
- Node.js 20+
- Git

## Build steps (PowerShell)

```powershell
git clone https://github.com/ATphobia22/PTDT-v33.git
cd PTDT-v33

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller

npm install

npm run electron:dist
```

Output: `release/PTDT v33 Engineering Desktop Setup 33.0.0.exe`

## Architecture

| Component | Role |
|-----------|------|
| `backend_build.py` | PyInstaller freeze of FastAPI backend |
| `electron/main.js` | Spawns `ptdt-backend.exe`, loads WebGPU UI |
| `electron/preload.js` | Safe bridge (`window.ptdt.apiBase`) |
| `backend/routers/grants.py` | Berm / BCA / BRIC grant evaluation API |

Backend listens on `http://127.0.0.1:8000`.
