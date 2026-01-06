import pandas as pd
from sklearn.metrics import classification_report
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# ==========================================
# CONFIGURATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "legalbert_clause_classifier")
CSV_PATH = os.path.join(MODELS_DIR, "prepared_data.csv")

# Column names from your file
TEXT_COL = "clause_text"
LABEL_COL = "clause_type"

# ==========================================
# 1. LOAD DATA & BUILD LABEL MAP
# ==========================================
print(f"📂 Loading data from: {CSV_PATH}")
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    print(f"✅ Loaded {len(df)} rows.")
else:
    print("❌ ERROR: Data file not found.")
    exit()

# --- CRITICAL FIX: REBUILD THE LABEL MAP ---
# We assume the model was trained on these labels sorted alphabetically.
# This converts ["Indemnity", "Liability"] -> {0: "Indemnity", 1: "Liability"}
unique_labels = sorted(df[LABEL_COL].dropna().unique().tolist())
id2label = {i: label for i, label in enumerate(unique_labels)}
label2id = {label: i for i, label in enumerate(unique_labels)}

print(f"🔧 Reconstructed Label Map ({len(id2label)} classes):")
print(f"   ID 0 -> {id2label[0]}")
print(f"   ID 1 -> {id2label[1]}")
print(f"   ... and {len(id2label)-2} more.")

# ==========================================
# 2. LOAD MODEL
# ==========================================
print(f"\n🤖 Loading model...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    print("✅ Model loaded.")
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit()

# ==========================================
# 3. RUN PREDICTIONS
# ==========================================
print("\n🔮 Running predictions on first 50 rows...")
sample_df = df.head(50).copy()

def predict(text):
    if not isinstance(text, str): return 0
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted_id = torch.argmax(logits, dim=1).item()
    return predicted_id

# 1. Get the ID (0, 1, 2...)
sample_df['predicted_id'] = sample_df[TEXT_COL].apply(predict)

# 2. Convert ID to Text using our new map
sample_df['predicted_label'] = sample_df['predicted_id'].map(id2label)

# ==========================================
# 4. REPORT
# ==========================================
print("\n" + "="*40)
print("       CORRECTED ACCURACY REPORT       ")
print("="*40)

# Compare Text vs Text
print(classification_report(
    sample_df[LABEL_COL], 
    sample_df['predicted_label'],
    zero_division=0
))

print("\nDEBUG CHECK:")
print(sample_df[[LABEL_COL, 'predicted_label']].head(5))