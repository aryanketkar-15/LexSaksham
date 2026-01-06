# LexSaksham API Documentation

## Base URL
- `http://localhost:5000`

## Endpoints

### POST `/analyze_clause`
- Classifies a clause into a legal category.
- Request JSON: `{ "text": "...", "lang": "en|hi|mr" }`
- Response JSON: `{ "predicted_clause_type": "Indemnity", "confidence": 0.912 }`

### POST `/assess_clause`
- Hybrid ML + rules risk scoring.
- Request JSON: `{ "text": "..." }`
- Response JSON: `{ "clause_type": "Indemnity", "risk_level": "High", "confidence": 0.93, "explanation": "...", "important_tokens": ["indemnify", "liability", ...] }`

### POST `/summarize_clause`
- Summarizes the clause in plain language.
- Request JSON: `{ "text": "...", "lang": "en|hi|mr" }`
- Response JSON: `{ "summary": "...", "model": "legal_t5_summarizer" }`
- Notes: For `lang=hi`, returns back-translated Hindi summary; Marathi returns English for now.

### POST `/explain_clause_shap`
- SHAP-style token importance (canonical JSON format).
- Request JSON: `{ "text": "..." }`
- Response JSON: `{ "model": "legalbert_clause_classifier", "predicted_class": 5, "class_name": "Indemnity", "tokens": ["The", "contractor", ...], "importance": [0.02, -0.03, ...], "method": "shap" }`

### POST `/explain_clause_lime`
- LIME token importance (canonical JSON format).
- Request JSON: `{ "text": "..." }`
- Response JSON: `{ "model": "legalbert_clause_classifier", "predicted_class": 5, "class_name": "Indemnity", "tokens": [...], "importance": [...], "method": "lime" }`

### POST `/search_judgment`
- Semantic search over FAISS index.
- Request JSON: `{ "query": "..." }`
- Response JSON: `{ "query": "...", "results": [{ "id": 123, "title": "...", "similarity": 0.83 }] }`

### POST `/upload_contract`
- Upload a PDF/DOCX contract; extracts clauses and runs full pipeline.
- Form-Data: `file` (PDF/DOCX)
- Response JSON: `{ "count": N, "results": [ { "clause_text": "...", "analysis": {"predicted_clause_type": "...", "confidence": 0.91}, "risk": { ... }, "summary": {"summary": "...", "model": "legal_t5_summarizer"}, "explainability": { "model": "legalbert_clause_classifier", "predicted_class": 5, "class_name": "Indemnity", "tokens": [...], "importance": [...], "method": "attention" } } ] }`

## Notes
- All endpoints return JSON and handle errors with HTTP status codes.
- GPU is used when available for speed.