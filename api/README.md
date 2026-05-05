# API Directory - FastAPI REST Server

## Purpose
FastAPI-based REST API server for the CvSU Virtual Assistant chatbot system.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Main FastAPI application with 15+ endpoints |
| `hybrid_chatbot.py` | Hierarchical hybrid chatbot (NB + NN) |
| `logger.py` | Chat logging to SQLite database |
| `__init__.py` | Python package marker |

## Starting the API

### Development
```bash
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Production
```bash
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker
```bash
docker-compose -f deployment/docker-compose.yml up -d
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/chat` | Send message, get response |
| GET | `/health` | Health check |
| GET | `/model/info` | Model performance stats |
| GET | `/logs/today` | Today's chat statistics |
| GET | `/logs/intents` | Intent usage breakdown |
| GET | `/docs` | Swagger UI documentation |

## Example Requests

### Chat Endpoint
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are admission requirements?",
    "user_id": "student_123"
  }'
```

### Response
```json
{
  "response": "For freshman admission to CvSU...",
  "intent": "admissions_requirements",
  "confidence": 0.758,
  "user_id": "student_123",
  "session_id": null
}
```

## Configuration

### Models Location
- Model path: `models/CvSU_classifier.pkl`
- Responses: `models/responses_map.json`

### Logging
- Database: `logs/chat_history.db`
- Backups: `logs/daily_backups/`

## Components

### HybridChatbot (hybrid_chatbot.py)
Hierarchical confidence-based routing:
1. Try Naive Bayes (fast) → 55% confidence threshold
2. If low confidence, try Neural Network → 50% threshold
3. If all low, use fallback response

### ChatLogger (logger.py)
Async SQLite logging:
- Captures user messages
- Logs bot responses
- Tracks intents and confidence
- Automatic daily JSON backups
- Real-time analytics queries

### REST Server (app.py)
FastAPI with:
- CORS enabled for web integration
- 15+ endpoints
- Automatic OpenAPI documentation
- Streaming responses for long text
- Pydantic validation

## Performance

| Metric | Value |
|--------|-------|
| Response Time | <75ms |
| Model Accuracy | 95.59% |
| Max Concurrent | Unlimited (asyncio) |
| Database | SQLite (file-based) |

## Troubleshooting

### API Won't Start
```bash
# Check if port is in use
lsof -i :8000

# Use different port
python -m uvicorn api.app:app --port 8001
```

### Model Not Loading
```bash
# Check models exist
ls -la ../models/

# Verify file permissions
chmod 644 ../models/*.pkl ../models/*.json
```

### Logs Database Error
```bash
# Check logs directory
ls -la ../logs/

# Reset database
rm ../logs/chat_history.db
```

## Deployment

### Local
```bash
python -m uvicorn api.app:app --port 8000
```

### Docker
```bash
docker-compose -f deployment/docker-compose.yml up -d
```

### Kubernetes (Future)
```bash
kubectl apply -f deployment/k8s-manifest.yaml
```

## Related Documentation

- **API Reference**: `docs/API_README.md`
- **Deployment**: `docs/DOCKER_DEPLOYMENT.md`
- **Architecture**: `docs/PROJECT_STATUS.md`
- **Integration**: `docs/INTEGRATION_GUIDE.md`

