# backend/ai_service/scripts/debug_predict.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path
import json, sys

# --- FIXED: use parents[1] so MODEL_DIR -> backend/ai_service/models/...
MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "legalbert_clause_classifier"

print("MODEL_DIR:", MODEL_DIR)
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

print("Device:", device)
print("Num labels (model.config.num_labels):", getattr(model.config, "num_labels", None))
print("id2label sample:", getattr(model.config, "id2label", None))

examples = [
    "The contractor shall indemnify the client for any damages.",
    "Either party may terminate this agreement on thirty days' notice.",
    "The supplier will not be liable for delay caused by force majeure.",
]

for s in examples:
    enc = tokenizer(s, return_tensors="pt", truncation=True, padding=True, max_length=256).to(device)
    with torch.no_grad():
        out = model(**enc)
    logits = out.logits
    probs = torch.nn.functional.softmax(logits, dim=-1).cpu().numpy()[0]
    pred_idx = int(probs.argmax())
    top5 = sorted(list(enumerate(probs)), key=lambda x: -x[1])[:5]
    print("\nTEXT:", s)
    print("LOGITS shape:", tuple(logits.shape))
    print("Top5 (idx,prob):", top5)
    print("Predicted idx:", pred_idx)

    # --- FIXED: read label_classes.json and index using str(pred_idx) if keys are strings ---
    label_map_file = MODEL_DIR / "label_classes.json"
    if label_map_file.exists():
        labels = json.load(open(label_map_file, "r", encoding="utf8"))
        human = labels.get(str(pred_idx)) or labels.get(pred_idx) or "N/A"
        print("Mapped label_classes.json ->", human)
    else:
        print("label_classes.json not found at", label_map_file)
