"""
generate_summarization_dataset.py
---------------------------------
Reads your existing train.jsonl (with id, text)
and auto-creates balanced plain-language summaries
for LegalT5 training.
Outputs:
  summarize_train.jsonl
  summarize_validation.jsonl
"""

import json, random, os, re
from pathlib import Path
from tqdm import tqdm
from sklearn.model_selection import train_test_split

# -------------------------------
# PATHS
# -------------------------------
DATA_DIR = Path(__file__).resolve().parents[1] / "datasets" / "clause_dataset" / "prepared"
SRC_FILE = DATA_DIR / "train.jsonl"
TRAIN_OUT = DATA_DIR / "summarize_train.jsonl"
VAL_OUT   = DATA_DIR / "summarize_validation.jsonl"

# -------------------------------
# HELPER: simple cleaner
# -------------------------------
def clean_text(t):
    if not t: return ""
    t = re.sub(r"\s+", " ", t)
    t = t.strip()
    return t

# -------------------------------
# HELPER: balanced summary generator
# (formal + simple style)
# -------------------------------
def make_summary(text):
    """
    Simple rule-based pseudo-summarizer to produce training pairs.
    You can later replace this logic with GPT-generated summaries.
    """
    t = clean_text(text)
    t = re.sub(r"^The\s+party\s+shall", "The party agrees to", t, flags=re.I)
    t = re.sub(r"\bshall\b", "must", t, flags=re.I)
    t = re.sub(r"\bupon\b", "after", t, flags=re.I)
    t = re.sub(r"hereby", "", t, flags=re.I)
    t = re.sub(r"agreement", "contract", t, flags=re.I)
    t = re.sub(r"confidential information", "private information", t, flags=re.I)
    t = re.sub(r"within\s+(\d+)\s+days", r"in \1 days", t, flags=re.I)
    t = re.sub(r"^\d+\.\s*", "", t)
    # remove redundancy
    if len(t.split()) > 22:
        t = " ".join(t.split()[:22]) + "..."
    # Add a prefix to make it read like a summary
    return "This clause means that " + t[0].lower() + t[1:] if t else ""

# -------------------------------
# LOAD SOURCE DATA
# -------------------------------
if not SRC_FILE.exists():
    raise SystemExit(f"❌ train.jsonl not found at {SRC_FILE}")

records = []
with open(SRC_FILE, "r", encoding="utf-8") as f:
    for line in f:
        try:
            item = json.loads(line)
            if not item.get("text"): continue
            item["summary"] = make_summary(item["text"])
            records.append(item)
        except json.JSONDecodeError:
            continue

print(f"✅ Loaded {len(records)} clauses from {SRC_FILE}")

# -------------------------------
# SPLIT (80/20)
# -------------------------------
train_records, val_records = train_test_split(records, test_size=0.2, random_state=42)

# -------------------------------
# WRITE OUTPUTS
# -------------------------------
for out_path, recs in [(TRAIN_OUT, train_records), (VAL_OUT, val_records)]:
    with open(out_path, "w", encoding="utf-8") as f:
        for r in recs:
            json.dump(r, f, ensure_ascii=False)
            f.write("\n")
    print(f"💾 Wrote {len(recs)} records → {out_path}")

print("\n🎉 Dataset generation complete.")
print(f"Train: {len(train_records)} | Validation: {len(val_records)}")
