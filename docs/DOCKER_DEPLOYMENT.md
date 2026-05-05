# CvSU Chatbot - Docker Deployment Guide

Deploy the CvSU Virtual Assistant using Docker for production environments.

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Navigate to project directory
cd c:/Users/user/Documents/POC/SeviAI

# Build and start the chatbot
docker-compose up -d

# View logs
docker-compose logs -f CvSU-chatbot

# Access the API
# http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Docker CLI

```bash
# Build the image
docker build -t CvSU-chatbot:latest .

# Run the container
docker run -d \
  --name CvSU-chatbot \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  CvSU-chatbot:latest

# View logs
docker logs -f CvSU-chatbot

# Stop the container
docker stop CvSU-chatbot

# Remove the container
docker rm CvSU-chatbot
```

## System Requirements

- Docker 20.10+
- Docker Compose 1.29+ (if using docker-compose)
- 1GB RAM minimum
- 500MB disk space for models and data

## Image Details

- **Base Image**: Python 3.11-slim
- **Model**: Naive Bayes (95.59% accuracy) + Neural Network (when trained)
- **Framework**: FastAPI with 15+ endpoints
- **Port**: 8000
- **Health Check**: Every 30 seconds

## Deployment Variants

### Development (Local)

```bash
# Run with reload for code changes
docker-compose -f docker-compose.dev.yml up
```

### Production

```bash
# Run in detached mode with 4 workers
docker-compose up -d

# Scale to multiple instances
docker-compose up -d --scale CvSU-chatbot=3
```

### With Neural Network

```bash
# Train NN first (requires Python 3.11/3.12 locally)
python train_hybrid.py

# Then build and deploy
docker-compose up --build -d
```

## Environment Variables

Edit `docker-compose.yml` to configure:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - WORKERS=4
  - LOG_LEVEL=INFO
```

## Volume Mounts

- `/app/models` - Trained model files
- `/app/data` - Intent definitions and training data
- `/app/logs` - Chat logs and analytics database

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "model_loaded": true}
```

### View Logs

```bash
docker-compose logs -f CvSU-chatbot
```

### Check Model Info

```bash
curl http://localhost:8000/model/info
```

### View Daily Analytics

```bash
curl http://localhost:8000/logs/today
```

## API Endpoints (in Container)

All endpoints available at `http://localhost:8000`:

- `POST /chat` - Chat with the bot
- `GET /health` - Health check
- `GET /model/info` - Model information
- `GET /logs/today` - Today's statistics
- `GET /logs/intents` - Intent usage
- `GET /docs` - Interactive API documentation

## Production Recommendations

1. **Reverse Proxy**: Use nginx for load balancing
   ```nginx
   upstream CvSU {
       server CvSU-chatbot:8000;
   }
   
   server {
       listen 80;
       server_name api.cvsu.edu.ph;
       
       location / {
           proxy_pass http://CvSU;
       }
   }
   ```

2. **Database Persistence**: Mount volumes to persist chat logs
   ```bash
   docker volume create CvSU-logs
   ```

3. **Scaling**: Use docker-compose to scale workers
   ```bash
   docker-compose up --scale CvSU-chatbot=4 -d
   ```

4. **Security**: Use .env file for secrets
   ```bash
   # .env
   API_KEY=your-secret-key
   ```

5. **Monitoring**: Integrate with Prometheus/Grafana
   ```yaml
   # Add metrics endpoint to app.py
   from prometheus_client import Counter, Histogram
   ```

## Troubleshooting

### Port Already in Use

```bash
# Use a different port
docker run -p 9000:8000 CvSU-chatbot:latest

# Or kill the process using 8000
lsof -i :8000
kill -9 <PID>
```

### Out of Memory

Increase Docker memory allocation:

```bash
# Docker Desktop settings or via CLI
docker update --memory 2g CvSU-chatbot
```

### Model Not Loading

Check logs for errors:

```bash
docker-compose logs | grep "FAILED\|ERROR"
```

Ensure model files exist:

```bash
docker exec CvSU-chatbot ls -la /app/models/
```

## Kubernetes Deployment

For K8s clusters, convert docker-compose to Kubernetes manifests:

```bash
# Install kompose
curl -L https://github.com/kubernetes/kompose/releases/download/v1.28.0/kompose-linux-amd64 -o kompose
chmod +x kompose

# Convert docker-compose to K8s manifests
./kompose convert -f docker-compose.yml
```

## Cleanup

```bash
# Remove containers
docker-compose down

# Remove images
docker rmi CvSU-chatbot:latest

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Prune all unused Docker resources
docker system prune -a
```

## Next Steps

1. Train the Neural Network (when Python 3.11/3.12 support available)
2. Set up monitoring with Prometheus/Grafana
3. Configure reverse proxy (nginx/Apache)
4. Deploy to Kubernetes for high availability
5. Set up CI/CD pipeline for automated deployments

---

**Iskolar para sa Bayan!** 🎓

For issues, check the logs and verify model files are present in the `/app/models` directory.

