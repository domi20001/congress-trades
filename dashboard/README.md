# Congress Trades Dashboard — React Edition

Vollständiges Dashboard mit FastAPI-Backend und React-Frontend.

## Einmalige Installation

```bash
# 1. Backend-Abhängigkeiten
cd backend
pip install -r requirements.txt --break-system-packages

# 2. Frontend-Abhängigkeiten (Node.js >= 18 vorausgesetzt)
cd ../frontend
npm install
```

## Starten

```bash
# Einzeiliger Start (beide Prozesse gleichzeitig):
bash start.sh

# Oder manuell:
# Terminal 1 — Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Dashboard öffnet sich unter: **http://localhost:5173**

## Datenbankpfad

Die `trades_history.db` muss eine Ebene über dem `dashboard/`-Ordner liegen —
also direkt neben deiner `app.py`:

```
projekt/
├── app.py
├── trades_history.db   ← hier!
├── import_kaggle.py
└── dashboard/
    ├── backend/
    └── frontend/
```

## Seiten

| URL | Inhalt |
|-----|--------|
| `/` | Übersicht mit KPIs, Signale, Top-Aktien |
| `/trades` | Alle Trades — filterbar, sortierbar |
| `/signals` | Kaufsignal-Detektor mit Kurschart |
| `/portfolios` | Rangliste nach Handelsvolumen |
| `/politicians` | Einzelansicht + Renditeberechnung |
| `/top-stocks` | Kaufdruck-Indikator + Kursverlauf |
| `/delay` | Meldeverzug-Analyse |

## Features

- Dark / Light Mode (persistent via localStorage)
- Alle Seiten vollständig responsiv
- Proxied API-Calls (kein CORS-Problem lokal)
- Kursdaten via Yahoo Finance (yfinance) — kein Key
- Logos via Clearbit (kein Key)
