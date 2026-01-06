# LexSaksham AI Service — Configuration & Calibration Guide

## 📋 What Was Added

### 1. **logging_utils.py** — Safe Atomic JSONL Logging
- `append_prediction_log(logpath, data_dict)`: Thread-safe append to predictions.jsonl
- `read_prediction_logs(logpath, limit=100)`: Read recent predictions for analysis
- Handles file creation, encoding, and sync automatically
- Logging failures do not crash requests (graceful degradation)

### 2. **calibrate_temperature.py** — Confidence Calibration
- Optimizes scalar temperature T to improve confidence calibration
- Reads validation set (JSONL format: `{"text": "...", "label": "LABEL_X" or "label_idx": 3}`)
- Collects logits from model, then minimizes NLL to find optimal T
- Outputs `temperature.json`: `{"temperature": 1.234}`
- Integration: `app.py` loads T at startup and uses it for scaling

### 3. **Enhanced app.py**
- Loads temperature from `TEMPERATURE_PATH` at startup
- New env vars: `ANALYSIS_CONFIDENCE_THRESHOLD`, `PREDICTION_LOG_PATH`, `TEMPERATURE_PATH`, `DEFAULT_EXPLAIN_METHOD`
- `/analyze_clause` now accepts optional `explain_method` parameter
- Logs each prediction to JSONL with full metadata including `temperature_applied`
- Safe logging: errors don't crash requests

### 4. **.env.example** — Configuration Reference
- Documents all env vars, defaults, and typical values
- Copy to `.env` and customize for your deployment

---

## 🚀 Quick Start

### Step 1: Prepare Validation Set (if you have one)

Your validation set should be JSONL format, one example per line:

```json
{"text": "The contractor shall indemnify the client for any damages.", "label": "LABEL_5"}
{"text": "This confidentiality clause covers all proprietary information.", "label": "LABEL_0"}
```

Or use `label_idx` instead of `label`:

```json
{"text": "The contractor shall indemnify the client for any damages.", "label_idx": 5}
```

**Don't have a validation set?** For now, skip to Step 3 and use T=1.0 (no scaling). Calibration improves over time.

### Step 2: Calibrate Temperature (Optional but Recommended)

```bash
# From backend/ai_service directory
python scripts/calibrate_temperature.py \
    --valset /path/to/validation.jsonl \
    --out ./models/temperature.json \
    --device cuda
```

**Output example:**
```
✅ Loaded 500 validation examples
📊 Optimal temperature T = 1.123
NLL before: 0.8234
NLL after:  0.7891
Improvement: 4.2%
Temperature saved to ./models/temperature.json
```

**Result:** `models/temperature.json` is created with optimal T. `app.py` will auto-load it on next restart.

### Step 3: Configure Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
# Set confidence threshold (default 0.6, try 0.7 for conservative)
ANALYSIS_CONFIDENCE_THRESHOLD=0.7

# Path to prediction log (auto-created if missing)
PREDICTION_LOG_PATH=./logs/predictions.jsonl

# Path to temperature (auto-created by calibration script)
TEMPERATURE_PATH=./models/temperature.json

# Default explainability method (attention is fastest)
DEFAULT_EXPLAIN_METHOD=attention
```

Or set directly in PowerShell before running:

```powershell
$env:ANALYSIS_CONFIDENCE_THRESHOLD="0.7"
$env:DEFAULT_EXPLAIN_METHOD="attention"
python backend/ai_service/app.py
```

### Step 4: Run the Service

```bash
cd backend/ai_service
python app.py
```

**Expected startup output:**
```
🚀 LexSaksham AI Service starting...
📦 Loading Clause Classification model...
✅ Clause Classification model loaded on GPU
📊 Loaded temperature scaling T = 1.123
⚙️ Starting Flask API on 0.0.0.0:5000 ...
```

---

## 🧪 Testing the Enhanced Endpoint

### Test 1: Analyze Clause with Default Explainability

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/analyze_clause' -Method Post `
  -Headers @{ 'Content-Type' = 'application/json' } `
  -Body '{"text":"The contractor shall indemnify the client for any damages.","lang":"en"}'
```

**Response example:**
```json
{
  "predicted_clause_type": "LABEL_13",
  "predicted_clause_name": "Obligations / Responsibilities",
  "confidence": 0.4625,
  "requires_review": true,
  "top_k": [
    {"label": "LABEL_13", "predicted_clause_name": "Obligations / Responsibilities", "confidence": 0.4625},
    {"label": "LABEL_5", "predicted_clause_name": "Indemnity / Liability", "confidence": 0.4603},
    {"label": "LABEL_14", "predicted_clause_name": "Payment Terms", "confidence": 0.0174}
  ],
  "explain_method": "attention",
  "suggestion": "Confidence 46.2% is below threshold 70.0%. Consider human review or check top_k alternatives."
}
```

### Test 2: Request with LIME Explainability

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/analyze_clause' -Method Post `
  -Headers @{ 'Content-Type' = 'application/json' } `
  -Body '{"text":"The contractor shall indemnify the client for any damages.","lang":"en","explain_method":"lime"}'
```

Response includes `"explain_method": "lime"` (if LIME is installed; otherwise "attention" with warning).

### Test 3: Check Prediction Logs

```powershell
# View last 5 log entries
Get-Content backend/ai_service/logs/predictions.jsonl -Tail 5 | ConvertFrom-Json
```

Each log entry includes:
- `timestamp`: ISO UTC time
- `input_text`: First 200 chars of clause
- `input_lang`: Language ("en", "hi", "mr")
- `predicted_label`: Raw LABEL_X
- `predicted_name`: Human-readable name
- `confidence`: Numeric score (0–1)
- `requires_review`: Boolean flag
- `top_k`: All 3 predictions
- `explain_method`: Method used (or requested)
- `temperature_applied`: T value applied

---

## 📊 Using Logs for Monitoring & Calibration

### Compute Confidence Calibration Metrics (ECE)

Once you have >100 predictions logged, compute Expected Calibration Error:

```python
import json
import numpy as np

# Load logs
predictions = []
with open("logs/predictions.jsonl", "r") as f:
    for line in f:
        predictions.append(json.loads(line))

# Bucket predictions by confidence ranges
buckets = {
    "0.0-0.2": [],
    "0.2-0.4": [],
    "0.4-0.6": [],
    "0.6-0.8": [],
    "0.8-1.0": []
}

for pred in predictions:
    conf = pred["confidence"]
    if conf < 0.2: buckets["0.0-0.2"].append(pred)
    elif conf < 0.4: buckets["0.2-0.4"].append(pred)
    elif conf < 0.6: buckets["0.4-0.6"].append(pred)
    elif conf < 0.8: buckets["0.6-0.8"].append(pred)
    else: buckets["0.8-1.0"].append(pred)

# Print stats per bucket
for bucket_name, items in buckets.items():
    if items:
        avg_conf = np.mean([p["confidence"] for p in items])
        num_review = sum(1 for p in items if p["requires_review"])
        print(f"{bucket_name}: avg_conf={avg_conf:.2f}, requires_review_count={num_review}, total={len(items)}")
```

### Analyze Most Common Clause Types

```python
from collections import Counter

pred_names = [p["predicted_name"] for p in predictions]
counts = Counter(pred_names)

for name, count in counts.most_common(10):
    print(f"{name}: {count}")
```

### Check Review Rate by Threshold

```python
thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
for t in thresholds:
    review_count = sum(1 for p in predictions if p["confidence"] < t)
    review_pct = review_count / len(predictions) * 100
    print(f"Threshold {t:.1f}: {review_pct:.1f}% require review")
```

---

## 🔧 Tuning Tips

### Confidence Threshold

- **0.5**: Aggressive (most high-confidence predictions auto-accepted, more misses)
- **0.6**: Balanced (default, good starting point)
- **0.7**: Conservative (many require review, fewer errors)
- **0.9**: Very strict (almost everything flagged for review)

**Recommendation:** Start at 0.6, then collect 50+ predictions and analyze accuracy per bucket. Adjust threshold to target 80–90% auto-accept rate with <5% error rate in auto-accepted predictions.

### Temperature Scaling

- If your predictions are **over-confident** (model thinks 0.95 when true acc is 0.7), T > 1.0 helps (widens the gap).
- If your predictions are **under-confident** (model thinks 0.5 when true acc is 0.8), T < 1.0 helps (narrows the gap).
- Calibration script automatically finds optimal T.

---

## 📝 Integration Checklist

- [ ] Deploy `logging_utils.py` to `backend/ai_service/`
- [ ] Deploy `scripts/calibrate_temperature.py` to `backend/ai_service/scripts/`
- [ ] Update `app.py` with new imports, env vars, and logging calls
- [ ] Create `.env` from `.env.example` and set your threshold
- [ ] (Optional) Run calibration script on validation set to get `models/temperature.json`
- [ ] Restart service and test `/analyze_clause` endpoint
- [ ] Verify predictions are being logged to `logs/predictions.jsonl`
- [ ] Monitor prediction logs and adjust threshold if needed

---

## 🚨 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError: temperature.json` | Calibration not run yet | Use T=1.0 (default), or run calibration script |
| Predictions not logged to JSONL | `PREDICTION_LOG_PATH` wrong or permission issue | Check path, ensure `logs/` dir is writable |
| All predictions have `requires_review: true` | Threshold too high | Lower `ANALYSIS_CONFIDENCE_THRESHOLD` |
| Calibration script fails with "No valid examples" | Validation set format wrong | Ensure JSONL has `text` and `label` or `label_idx` keys |
| Temperature not loading at startup | `temperature.json` is malformed JSON | Re-run calibration script |

---

## 📚 Files Changed/Created

| File | Change |
|------|--------|
| `backend/ai_service/app.py` | Added env var loading, temperature scaling, logging_utils integration, explain_method param |
| `backend/ai_service/logging_utils.py` | NEW: Safe atomic JSONL logging |
| `backend/ai_service/scripts/calibrate_temperature.py` | NEW: Temperature calibration script |
| `backend/ai_service/.env.example` | NEW: Configuration template |
| `backend/ai_service/requirements.txt` | (No change needed unless adding scipy for calibration) |

---

## ✨ Next Steps (After Testing)

1. Push code changes to git
2. Collect 100+ predictions over 1–2 weeks
3. Run calibration script on validation subset
4. Analyze logs for accuracy per confidence bucket
5. Adjust threshold based on your acceptable error rate
6. (Optional) Integrate calibration script into CI/CD pipeline to auto-calibrate monthly

