@echo off
echo Starting CvSU Chatbot API Server...
echo.
python -m uvicorn app:app --host 0.0.0.0 --port 8000
pause
