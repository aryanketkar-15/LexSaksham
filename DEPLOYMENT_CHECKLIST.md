# ✅ Implementation Checklist & Deployment Steps

## 🎯 Immediate Actions (Do These Now)

- [x] ✅ Created `logging_utils.py` (atomic JSONL logging)
- [x] ✅ Created `calibrate_temperature.py` (temperature optimization)
- [x] ✅ Updated `app.py` (temperature scaling, env vars, logging integration)
- [x] ✅ Created `.env.example` (configuration reference)
- [x] ✅ Created `CALIBRATION_GUIDE.md` (complete setup guide)
- [x] ✅ Updated `requirements.txt` (added shap, lime, sentencepiece)

## 🚀 Deployment Steps (Do These Next)

### Step 1: Install Missing Dependencies
```powershell
cd C:\Users\aryan\lexsaksham
pip install -r backend/ai_service/requirements.txt
```

### Step 2: Copy Configuration
```powershell
# Copy to workspace root for reference
Copy-Item backend/ai_service/.env.example .env.example
```

### Step 3: Restart Service with Threshold
```powershell
$env:ANALYSIS_CONFIDENCE_THRESHOLD="0.7"
python backend/ai_service/app.py
```

**Expected output:**
```
🚀 LexSaksham AI Service starting...
📦 Loading Clause Classification model...
✅ Clause Classification model loaded on GPU
📂 Loading FAISS index for fast retrieval...
✅ FAISS index loaded with X entries.
⚙️ Starting Flask API on 0.0.0.0:5000 ...
```

### Step 4: Test Endpoint
```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/analyze_clause' -Method Post `
  -Headers @{ 'Content-Type' = 'application/json' } `
  -Body '{"text":"The contractor shall indemnify the client for any damages.","lang":"en"}'
```

**Verify response includes:**
- `predicted_clause_type`: LABEL_X
- `predicted_clause_name`: Human-readable name
- `confidence`: 0.0–1.0
- `requires_review`: true/false
- `top_k`: Array of 3 alternatives
- `explain_method`: "attention" or requested method

### Step 5: Verify Logging
```powershell
Get-Content backend/ai_service/logs/predictions.jsonl -Tail 1 | ConvertFrom-Json
```

**Should show a JSON object with keys:**
- timestamp, input_text, input_lang
- predicted_label, predicted_name, confidence
- requires_review, top_k, explain_method, temperature_applied

## 📈 Optional: Calibration (If You Have Validation Data)

### Step 6: Prepare Validation Set
Create `validation.jsonl` with format:
```json
{"text": "The contractor shall indemnify the client for any damages.", "label": "LABEL_5"}
{"text": "This agreement is confidential and proprietary.", "label": "LABEL_0"}
```

### Step 7: Run Calibration
```powershell
python backend/ai_service/scripts/calibrate_temperature.py `
    --valset C:\path\to\validation.jsonl `
    --out backend/ai_service/models/temperature.json `
    --device cuda
```

**Expected output:**
```
✅ Loaded 500 validation examples
📊 Optimal temperature T = 1.123
NLL before: 0.8234
NLL after:  0.7891
Improvement: 4.2%
Temperature saved to ./models/temperature.json
```

### Step 8: Restart Service (Temperature Loads Auto)
```powershell
$env:ANALYSIS_CONFIDENCE_THRESHOLD="0.7"
python backend/ai_service/app.py
```

**Expected output includes:**
```
📊 Loaded temperature scaling T = 1.123
```

## 📊 Monitoring & Analysis (After 50+ Predictions)

### Step 9: Analyze Predictions
```powershell
# Read logs
$predictions = Get-Content backend/ai_service/logs/predictions.jsonl | ConvertFrom-Json

# Count predictions
$predictions.Count

# Check requires_review rate
($predictions | Where-Object { $_.requires_review -eq $true }).Count / $predictions.Count * 100

# Top clause types
$predictions | Group-Object { $_.predicted_name } | Sort-Object Count -Desc | Select-Object -First 10
```

### Step 10: Adjust Threshold (If Needed)
Based on analysis, adjust threshold:
```powershell
# More strict (more require review)
$env:ANALYSIS_CONFIDENCE_THRESHOLD="0.75"

# More aggressive (fewer require review)
$env:ANALYSIS_CONFIDENCE_THRESHOLD="0.65"

python backend/ai_service/app.py
```

## 🔄 Continuous Monitoring

### Daily
- [ ] Check service is running: `curl http://localhost:5000/`
- [ ] Monitor error logs if any

### Weekly
- [ ] Review predictions log size: `Get-Item backend/ai_service/logs/predictions.jsonl | Select-Object Length`
- [ ] Check for patterns in `requires_review` rate

### Monthly
- [ ] Analyze accuracy per confidence bucket
- [ ] Re-run calibration if validation data available
- [ ] Adjust threshold based on user feedback

## 🐛 Troubleshooting

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'X'` | Run `pip install -r requirements.txt` |
| Predictions not logged | Check `logs/` directory permissions and PREDICTION_LOG_PATH |
| All requires_review=true | Threshold too high; lower ANALYSIS_CONFIDENCE_THRESHOLD |
| Temperature not loading | Verify models/temperature.json exists and is valid JSON |
| Service crashes on request | Check app logs, may be missing optional package (LIME, etc.) |

## ✨ Success Indicators

Your deployment is successful when:

1. ✅ Service starts without import errors
2. ✅ `/analyze_clause` returns required fields (predicted_clause_type, confidence, requires_review, top_k)
3. ✅ Predictions are logged to `logs/predictions.jsonl` (one JSON per line)
4. ✅ Human-readable clause names appear (not just LABEL_X)
5. ✅ `requires_review` flag is set correctly based on threshold
6. ✅ Optional `explain_method` parameter is respected
7. ✅ (If calibrated) Temperature loads at startup and is logged

## 📞 Support

If issues arise:
1. Check `CALIBRATION_GUIDE.md` for detailed setup instructions
2. Review `IMPLEMENTATION_SUMMARY.md` for feature overview
3. Check app.py startup logs for error messages
4. Verify `requirements.txt` is fully installed

---

**Deployment Status: READY TO GO** 🚀

Next: Run the service and collect real predictions for monitoring!
