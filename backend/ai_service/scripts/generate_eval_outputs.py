import json, argparse, numpy as np
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

parser = argparse.ArgumentParser()
parser.add_argument("--test", required=True, help="path to test.jsonl")
parser.add_argument("--outdir", default="backend/ai_service/results", help="output folder")
# NEW: Add an argument to specify the model directory
parser.add_argument("--model_path", default=None, help="path to the trained model directory")
args = parser.parse_args()

# LOGIC: If user provides a path, use it. Otherwise, fallback to default.
if args.model_path:
    MODEL_DIR = Path(args.model_path)
else:
    # Default fallback (original behavior)
    MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "legalbert_clause_classifier"

print(f"Loading model from: {MODEL_DIR}") # Print this to be sure!

tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

texts = []
labels = []
with open(args.test, "r", encoding="utf8") as f:
    for i, line in enumerate(f):
        j = json.loads(line)
        if "text" not in j or "label" not in j:
            raise SystemExit(f"Line {i+1} missing 'text' or 'label' field")
        texts.append(j["text"])
        labels.append(int(j["label"]))

batch = 32
logits_list = []
print(f"Evaluating {len(texts)} samples...")

for i in range(0, len(texts), batch):
    batch_texts = texts[i:i+batch]
    enc = tokenizer(batch_texts, return_tensors="pt", truncation=True, padding=True, max_length=256)
    enc = {k: v.to(device) for k, v in enc.items()}
    with torch.no_grad():
        out = model(**enc)
    logits = out.logits.cpu().numpy()
    logits_list.append(logits)

logits_all = np.vstack(logits_list)
labels_np = np.array(labels, dtype=int)

outdir = Path(args.outdir)
outdir.mkdir(parents=True, exist_ok=True)
np.save(outdir / "logits.npy", logits_all)
np.save(outdir / "labels.npy", labels_np)
print("Saved logits.npy and labels.npy to", outdir)
print("logits shape:", logits_all.shape, "labels shape:", labels_np.shape)