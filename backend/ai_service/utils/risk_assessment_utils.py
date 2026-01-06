import json
import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path

# ---------- Load Rule-Based Keywords ----------
RULES_PATH = Path(__file__).parent.parent / "models" / "risk_assessment" / "rule_keywords.json"
with open(RULES_PATH, "r") as f:
    RISK_RULES = json.load(f)

# ---------- Load LegalBERT Clause Classifier ----------
CLAUSE_MODEL_PATH = Path(__file__).parent.parent / "models" / "legalbert_clause_classifier"
tokenizer = AutoTokenizer.from_pretrained(CLAUSE_MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(CLAUSE_MODEL_PATH)
model.to("cuda" if torch.cuda.is_available() else "cpu")
model.eval()

# ---------- Helper: rule-based keyword scoring ----------
def rule_score(text: str):
    text_lower = text.lower()
    scores = {"High": 0, "Medium": 0, "Low": 0}
    for level, keywords in RISK_RULES.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                scores[level] += 1
    # pick max nonzero else Low
    if all(v == 0 for v in scores.values()):
        return "Low", 0
    level = max(scores, key=scores.get)
    return level, scores[level]

# ---------- Combine ML + Rules ----------
def assess_clause(text: str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    conf, label_id = torch.max(probs, dim=1)
    label_map_path = CLAUSE_MODEL_PATH / "label_classes.json"
    label_map = json.load(open(label_map_path))
    label = label_map[str(label_id.item())]

    rule_level, _ = rule_score(text)

    # combine
    if rule_level == "High" or conf.item() > 0.9:
        final_level = "High"
    elif rule_level == "Medium" or 0.7 < conf.item() <= 0.9:
        final_level = "Medium"
    else:
        final_level = "Low"

    explanation = f"Predicted as {label} ({conf.item():.2f}). "
    explanation += f"Rule-based cues → {rule_level} risk." if rule_level else "No high-risk terms found."

    return {
        "clause_type": label,
        "risk_level": final_level,
        "confidence": round(conf.item(), 3),
        "explanation": explanation
    }
