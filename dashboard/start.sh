#!/bin/bash
# start.sh — startet Backend (FastAPI) und Frontend (React/Vite) gleichzeitig

echo "🏛️  Congress Trades Dashboard"
echo "=============================="
echo ""

# Backend
echo "▶ Starte Backend auf http://localhost:8000 …"
cd "$(dirname "$0")/backend"
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Frontend
echo "▶ Starte Frontend auf http://localhost:5173 …"
cd "$(dirname "$0")/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Dashboard läuft!"
echo "   → http://localhost:5173"
echo ""
echo "Zum Beenden: Ctrl+C"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
