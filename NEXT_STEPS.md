# LexSaksham — Next Steps

## Multilingual (Phase A)
- Verify translate-first pipeline with Hindi input end-to-end (analyze/summarize).
- Add Marathi back-translation helper (`en→mr`) for summaries.
- Cache translation models on first use; measure latency and GPU memory.
- Prepare evaluation sets for Hindi/Marathi and track metrics.

## Explainability (Phase B)
- Use attention-based explanations as primary in frontend (canonical JSON).
- Wire token-to-text mapping in React to avoid subword artifacts.
- Keep LIME/SHAP as optional fallback; add toggles in ExplainabilityView.

## Frontend (Phase C)
- Implement `UploadArea` to call `/upload_contract` and render results list.
- Build `LawyerDashboard` view with tabs: Analyze, Summarize, Search, Explain.
- Add `JudgmentCard` component for FAISS search results.
- Polish UX: spinners, errors, and per-action latency indicators.

## Evaluation & Paper
- Run `evaluate_classifier.py`, `evaluate_summarizer.py`, `evaluate_faiss.py` and store JSON in `backend/ai_service/results/`.
- Create `results/summary_table.md` consolidating headline metrics.
- Design ablations: batch size, fp16, beam width for summarizer.

## Deployment & Reproducibility
- Add a `requirements.txt` snapshot and `start_api.ps1` for Windows.
- Provide `MODEL_README.md` with paths and expected structure.
- Optional: Dockerfile for backend (CUDA base image) + compose.

## User Testing
- Pilot with 5–10 real contracts; collect feedback on clause types, summaries, and risk labels.
- Iterate on regex clause splitting and risk keyword rules.