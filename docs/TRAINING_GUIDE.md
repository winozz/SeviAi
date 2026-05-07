# CvSU Chatbot - Automated Training Guide

Train and improve your chatbot by sending diverse API requests and automatically expanding training patterns.

## Quick Start

### Option 1: Quick Test (Recommended First Step)

```bash
# Terminal 1: Start API
python -m uvicorn app:app --host 0.0.0.0 --port 8000

# Terminal 2: Run tests
python training/test_intents.py 8000 5
```

**What it does**: Tests each of 22 intents with 5 random queries (110 total requests) and reports:
- Overall accuracy
- Per-intent performance
- Weak intents that need improvement
- Saves detailed results to `intent_test_results.json`

**Example Output**:
```
[STATS] Overall:
   Accuracy: 44.55% (49/110)
   
Weak Intents (16):
   - about_CvSU: 0% accuracy
   - academic_calendar: 0% accuracy
   - goodbye: 0% accuracy
   
Recommendations:
   1. Run: python training/expand_intents.py
   2. Add more diverse patterns
   3. Retrain: python training/train_naive_bayes.py
```

---

## Training Scripts

### 1. test_intents.py - Quick Evaluation

**Purpose**: Rapidly test all intents to identify weak areas

**Usage**:
```bash
python training/test_intents.py [PORT] [QUERIES_PER_INTENT]
```

**Parameters**:
- `PORT`: API port (default: 8001)
- `QUERIES_PER_INTENT`: Number of test queries per intent (default: 5)

**Examples**:
```bash
# Quick test (5 queries per intent = 110 total)
python training/test_intents.py 8000 5

# Comprehensive test (10 queries per intent = 220 total)
python training/test_intents.py 8000 10

# Very thorough (20 queries = 440 total)
python training/test_intents.py 8000 20
```

**Output**:
- Console report with per-intent accuracy
- `intent_test_results.json` with detailed metrics
- Identifies intents performing below 80%

**Time**: ~4s for 110 requests, scales linearly

---

### 2. expand_intents.py - Pattern Expansion

**Purpose**: Automatically expand training patterns for weak intents

**Usage**:
```bash
python training/expand_intents.py
```

**What it does**:
1. Loads `data/cavsu_intents.json`
2. Analyzes each intent
3. Generates 5-15 new pattern variations
4. Saves to `data/cavsu_intents_expanded.json`

**Example additions**:
```
admissions_requirements
  Original: 20 patterns
  Expanded: 28 patterns
  
tuition_fees
  Original: 19 patterns
  Expanded: 27 patterns
```

**Next steps after running**:
```bash
# Replace original with expanded version
mv data/cavsu_intents_expanded.json data/cavsu_intents.json

# Retrain model with new patterns
python training/train_naive_bayes.py

# Restart API to load new model
python -m uvicorn app:app --port 8000
```

---

### 3. api_stress_test.py - Advanced Testing

**Purpose**: Send 100s-1000s of diverse queries to thoroughly train and test

**Prerequisites**:
```bash
pip install aiohttp
```

**Usage**:
```bash
python training/api_stress_test.py [TOTAL_REQUESTS] [PORT]
```

**Parameters**:
- `TOTAL_REQUESTS`: Total API requests (default: 500)
- `PORT`: API port (default: 8001)

**Examples**:
```bash
# Medium test (500 requests)
python training/api_stress_test.py 500 8000

# Heavy test (1000 requests)
python training/api_stress_test.py 1000 8000

# Intensive training (5000 requests)
python training/api_stress_test.py 5000 8000
```

**Features**:
- ✓ Async requests for speed
- ✓ 50 queries per batch
- ✓ Per-intent statistics
- ✓ Confidence score tracking
- ✓ Detailed JSON results

**Output**:
```
[Batch 1] Sending 50 requests... [45/50] (Total: 45/500)
[Batch 2] Sending 50 requests... [48/50] (Total: 93/500)
...
[STATS] Overall Performance:
   Total Requests: 500
   Correct: 420
   Incorrect: 80
   Accuracy: 84.00%
```

---

### 4. automated_training.py - Full Pipeline

**Purpose**: Complete training workflow (test → analyze → expand → retrain → verify)

**Usage**:
```bash
python training/automated_training.py [PORT]
```

**What it does** (6 steps):
1. ✓ Starts API on specified port
2. ✓ Tests all intents (10 queries each)
3. ✓ Analyzes weak intents
4. ✓ Automatically expands patterns
5. ✓ Retrains Naive Bayes model
6. ✓ Verifies improvements

**Example**:
```bash
# Start full automated training pipeline
python training/automated_training.py 8000
```

**Output**:
```
========================================
  AUTOMATED TRAINING PIPELINE
========================================

[Step 1/6] Starting API on port 8000...
   Waiting for API to initialize... [OK]

[Step 2/6] Testing intents...
   Overall Accuracy: 85.5%

[Step 3/6] Analyzing results...
   Weak Intents: 3
   - intent_1: 60%
   - intent_2: 65%
   - intent_3: 70%

[Step 4/6] Expanding training patterns...
   Total patterns: 227 → 285 (+25%)

[Step 5/6] Retraining model...
   Training Accuracy: 96.2%

[Step 6/6] Verifying improvement...
   New Accuracy: 89.2%

========================================
  RESULTS
========================================
   Baseline Accuracy: 85.5%
   Final Accuracy:    89.2%
   Improvement:       +3.7%

[SUCCESS] Model improved successfully!
```

---

## Complete Training Workflow

### Step-by-Step Process

**Terminal 1** (Keep API running):
```bash
# Start API
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

**Terminal 2** (Training commands):

```bash
# Step 1: Quick baseline test
python training/test_intents.py 8000 5

# Step 2: Analyze results
cat intent_test_results.json

# Step 3: Expand weak patterns
python training/expand_intents.py
mv data/cavsu_intents_expanded.json data/cavsu_intents.json

# Step 4: Retrain model
python training/train_naive_bayes.py

# Step 5: Restart API (kill in Terminal 1, restart)
# Or in a new terminal:
python -m uvicorn app:app --host 0.0.0.0 --port 8000

# Step 6: Verify improvements
python training/test_intents.py 8000 10
```

---

## Understanding Test Results

### Accuracy Interpretation

```
[STATS] Overall:
   Accuracy: 85.5% (150/175)
   Time: 8.3s
```

- **Accuracy**: Percentage of correctly classified queries
- **Numerator**: Queries classified to correct intent
- **Denominator**: Total queries tested
- **Time**: API response time (lower is better)

### Per-Intent Breakdown

```
Intent                             Accuracy     Avg Conf
------------------------------------------------------------
admissions_requirements               100% [OK]       75.3%
tuition_fees                          100% [OK]       70.3%
greeting                               60% [WARN]       43.6%
about_CvSU                             0% [FAIL]        0.0%
```

**Status Indicators**:
- `[OK]` - 80%+ accuracy (good)
- `[WARN]` - 60-79% accuracy (needs work)
- `[FAIL]` - <60% accuracy (critical)

### Confidence Scores

- **0.0-0.5**: Fallback response triggered
- **0.5-0.7**: Low confidence, may be incorrect
- **0.7-0.8**: Moderate confidence, usually correct
- **0.8-1.0**: High confidence, very likely correct

---

## Improvement Checklist

```
□ Run baseline test: python training/test_intents.py 8000 5
□ Review weak intents in results
□ Expand patterns: python training/expand_intents.py
□ Retrain model: python training/train_naive_bayes.py
□ Restart API with new model
□ Run verification test: python training/test_intents.py 8000 10
□ Compare before/after accuracy
□ Commit improved model: git add models/ && git commit
□ Deploy: docker-compose up --build -d
```

---

## Common Scenarios

### Scenario 1: Quick Model Check

```bash
python training/test_intents.py 8000 5
```

**Time**: ~5 seconds  
**Requests**: 110  
**Use when**: You want a quick snapshot of model performance

---

### Scenario 2: Identify Weak Areas

```bash
python training/test_intents.py 8000 10
```

**Time**: ~10 seconds  
**Requests**: 220  
**Use when**: You need reliable data on which intents need improvement

---

### Scenario 3: Train & Improve

```bash
# Terminal 1: Start API
python -m uvicorn app:app --port 8000

# Terminal 2: Full workflow
python training/automated_training.py 8000
```

**Time**: ~2 minutes  
**Requests**: ~260 test + ~50 expand + ~260 verify  
**Use when**: You want automated end-to-end improvement

---

### Scenario 4: Stress Testing (Advanced)

```bash
# Install if needed
pip install aiohttp

# Send 1000 requests in batches
python training/api_stress_test.py 1000 8000
```

**Time**: ~3-5 minutes  
**Requests**: 1000  
**Use when**: You need extensive training data or want to validate stability

---

## Data Files Generated

After running tests, you'll have:

```
intent_test_results.json
├── timestamp
├── overall_accuracy
├── total_requests
├── elapsed_seconds
└── per_intent
    ├── intent_name
    ├── accuracy
    ├── avg_confidence
    └── sample_responses

stress_test_results.json (if using api_stress_test.py)
├── similar structure
├── more detailed metrics
└── confidence distributions
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'aiohttp'"

For `api_stress_test.py`:
```bash
pip install aiohttp
```

For basic testing, use `test_intents.py` instead (requires only `requests`).

### API Not Responding

```bash
# Check if API is running
curl http://127.0.0.1:8000/health

# If not, start it
python -m uvicorn app:app --port 8000

# Check logs
tail -f /tmp/test_api.log
```

### Low Accuracy After Changes

```bash
# Check if model was retrained
ls -lh models/CvSU_classifier.pkl

# Verify intents.json was updated
wc -l data/cavsu_intents.json

# If old, retrain:
python training/train_naive_bayes.py
```

### "Port already in use"

```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
python -m uvicorn app:app --port 8001
```

---

## Performance Benchmarks

| Operation | Time | Requests | Accuracy |
|-----------|------|----------|----------|
| Quick test | 5s | 110 | Baseline |
| Comprehensive test | 15s | 330 | Better estimate |
| Expand patterns | 3s | N/A | N/A |
| Retrain model | 8s | N/A | Improved |
| Full pipeline | 120s | ~500 | Final |

---

## Next Steps

1. **Try it now**:
   ```bash
   python training/test_intents.py 8000 5
   ```

2. **Review results**: Check `intent_test_results.json`

3. **Identify weak intents**: Which ones scored <80%?

4. **Expand patterns**:
   ```bash
   python training/expand_intents.py
   mv data/cavsu_intents_expanded.json data/cavsu_intents.json
   ```

5. **Retrain**:
   ```bash
   python training/train_naive_bayes.py
   ```

6. **Verify improvement**:
   ```bash
   python training/test_intents.py 8000 10
   ```

---

## Advanced Usage

### Continuous Training Loop

```bash
#!/bin/bash
for i in {1..5}; do
  echo "Iteration $i"
  python training/test_intents.py 8000 10
  python training/expand_intents.py
  mv data/cavsu_intents_expanded.json data/cavsu_intents.json
  python training/train_naive_bayes.py
  sleep 5
done
```

### CSV Export Analysis

```bash
python << 'EOF'
import json

with open("intent_test_results.json") as f:
    data = json.load(f)

print("intent,accuracy,avg_confidence")
for intent, stats in data["per_intent"].items():
    print(f"{intent},{stats['accuracy']:.1f},{stats['avg_confidence']:.3f}")
EOF
```

---

## Summary

| Script | Purpose | Time | Use Case |
|--------|---------|------|----------|
| `test_intents.py` | Quick evaluation | 5-30s | Identify weak intents |
| `expand_intents.py` | Pattern generation | 3s | Improve training data |
| `train_naive_bayes.py` | Model retraining | 8s | Finalize improvements |
| `api_stress_test.py` | Advanced testing | 2-5m | Comprehensive validation |
| `automated_training.py` | Full pipeline | 2m | Complete workflow |

---

**"Iskolar para sa Bayan!"** 🎓

Your chatbot is ready to be trained. Start with `test_intents.py` to see current performance, then use the other scripts to improve!

