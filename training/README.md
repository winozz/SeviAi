# Training Directory - Model Development & Testing

## Purpose
Scripts for training, testing, and improving the ML model.

## Scripts Overview

| Script | Time | Requests | Purpose |
|--------|------|----------|---------|
| `train_naive_bayes.py` | 8s | N/A | Train Naive Bayes model |
| `train_hybrid.py` | 2m | N/A | Train Neural Network (requires Python 3.11) |
| `test_intents.py` | 5-30s | 110-220 | Quick intent evaluation |
| `expand_intents.py` | 3s | N/A | Auto-expand training patterns |
| `api_stress_test.py` | 2-5m | 500-5000 | Advanced async stress testing |
| `automated_training.py` | 2m | ~500 | Full training pipeline |
| `test_chatbot.py` | 30s | ~50 | Basic model validation |

## Quick Start

### Test Current Model
```bash
# Start API in another terminal
cd ..
python -m uvicorn api.app:app --port 8000

# Quick evaluation
python training/test_intents.py 8000 5
```

### Improve Model
```bash
# 1. Test current
python training/test_intents.py 8000 5

# 2. Expand patterns
python training/expand_intents.py
mv ../data/CvSU_intents_expanded.json ../data/CvSU_intents.json

# 3. Retrain
python training/train_naive_bayes.py

# 4. Verify (restart API first)
python training/test_intents.py 8000 10
```

## Detailed Scripts

### train_naive_bayes.py
Train Naive Bayes classifier on intents.

```bash
python training/train_naive_bayes.py
```

**Output**:
- `models/CvSU_classifier.pkl` - Trained model
- Console report with accuracy metrics
- Per-intent performance breakdown

**What it does**:
1. Load intents from `data/CvSU_intents.json`
2. Preprocess patterns (lowercase, tokenize, lemmatize)
3. Create TF-IDF vectorizer + Naive Bayes pipeline
4. Train on all patterns
5. Save model and responses

### test_intents.py
Quick evaluation across all intents.

```bash
python training/test_intents.py [PORT] [QUERIES_PER_INTENT]

# Examples
python training/test_intents.py 8000 5   # Quick: 110 requests
python training/test_intents.py 8000 10  # Medium: 220 requests
python training/test_intents.py 8000 20  # Thorough: 440 requests
```

**Output**:
- Per-intent accuracy percentages
- Average confidence scores
- Weak intents (<80% accuracy)
- `intent_test_results.json` with detailed metrics

### expand_intents.py
Auto-generate pattern variations.

```bash
python training/expand_intents.py
```

**Output**:
- `data/CvSU_intents_expanded.json`
- Console report showing pattern counts
- Next steps to integrate

**Then integrate**:
```bash
mv ../data/CvSU_intents_expanded.json ../data/CvSU_intents.json
python training/train_naive_bayes.py
```

### api_stress_test.py
Advanced async stress testing (requires aiohttp).

```bash
pip install aiohttp

python training/api_stress_test.py [TOTAL_REQUESTS] [PORT]

# Examples
python training/api_stress_test.py 500 8000   # Medium load
python training/api_stress_test.py 1000 8000  # Heavy load
python training/api_stress_test.py 5000 8000  # Intensive training
```

**Output**:
- Batch-by-batch progress
- Per-intent statistics
- `stress_test_results.json`
- Confidence distributions

### automated_training.py
Full pipeline: Test → Analyze → Expand → Retrain → Verify.

```bash
python training/automated_training.py [PORT]

# Example
python training/automated_training.py 8000
```

**Steps**:
1. [Step 1/6] Start API
2. [Step 2/6] Run tests (10 queries per intent)
3. [Step 3/6] Analyze weak intents
4. [Step 4/6] Expand patterns
5. [Step 5/6] Retrain model
6. [Step 6/6] Verify improvements

**Output**:
- Before/after accuracy comparison
- Recommendations
- Model improvement percentage

## Training Workflow

### Basic Training
```
Test (5min) → Analyze (2min) → Retrain (1min) → Verify (5min)
```

### Advanced Training
```
Test (5min) → Expand (2min) → Retrain (2min) → Stress Test (5min) → Verify (5min)
```

## Performance Metrics

### Accuracy Targets
- Good: >90%
- Acceptable: >80%
- Needs work: <80%

### Confidence Interpretation
- 0.0-0.5: Fallback triggered (low confidence)
- 0.5-0.7: Low confidence (may be incorrect)
- 0.7-0.8: Good confidence (usually correct)
- 0.8-1.0: High confidence (very likely correct)

## Results Files

After running tests, you get:

### intent_test_results.json
```json
{
  "timestamp": "2026-05-05T12:00:00",
  "overall_accuracy": 0.855,
  "total_requests": 110,
  "per_intent": {
    "admissions_requirements": {
      "accuracy": 1.0,
      "avg_confidence": 0.753
    }
  }
}
```

### stress_test_results.json
Similar structure with more detailed metrics and confidence distributions.

## Continuous Training

### Run Multiple Iterations
```bash
for i in {1..5}; do
  echo "Iteration $i"
  python test_intents.py 8000 5
  python expand_intents.py
  mv ../data/CvSU_intents_expanded.json ../data/CvSU_intents.json
  python train_naive_bayes.py
  sleep 2
done
```

## Troubleshooting

### API Not Responding
```bash
# Check if running
curl http://127.0.0.1:8000/health

# Start if needed
python -m uvicorn api.app:app --port 8000
```

### "ModuleNotFoundError: aiohttp"
```bash
# For stress test
pip install aiohttp

# Or use test_intents.py instead (no aiohttp needed)
python test_intents.py 8000 5
```

### Model Not Improving
1. Check if patterns are actually expanded:
   ```bash
   wc -l ../data/CvSU_intents.json
   ```

2. Review which intents are weak:
   ```bash
   cat intent_test_results.json | grep -A5 '"accuracy": 0'
   ```

3. Manually add more patterns to those weak intents

4. Retrain and test again

## Related Documentation

- **Full Training Guide**: `docs/TRAINING_GUIDE.md`
- **Model Status**: `docs/PROJECT_STATUS.md`
- **Architecture**: `docs/HYBRID_GUIDE.md`

