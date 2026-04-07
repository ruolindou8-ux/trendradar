@echo off
set PORT=8000
python -m uvicorn trendradar.api.app:app --host 0.0.0.0 --port %PORT%
pause
