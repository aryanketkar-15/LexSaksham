import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# CONFIGURATION
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "risk_assessment")

print(f"📂 Loading Risk Model from: {MODEL_PATH}")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    print("✅ Risk Model loaded successfully!")
    print(f"   Model expects {model.config.num_labels} labels.")
except Exception as e:
    print(f"❌ Error loading Risk Model: {e}")
    print("   If this fails, it might not be a BERT model (could be a pickle file?).")
    exit()

# TEST PREDICTION
test_text = "The Service Provider shall be liable for all damages without limitation."
print(f"\n🧪 Testing with: '{test_text}'")

inputs = tokenizer(test_text, return_tensors="pt", truncation=True, max_length=512)
with torch.no_grad():
    logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=1)[0]
    pred_id = torch.argmax(logits, dim=1).item()

print(f"   👉 Predicted ID: {pred_id}")
print(f"   👉 Confidence: {probs[pred_id].item():.4f}")

# CHECK LABELS
if hasattr(model.config, 'id2label') and model.config.id2label:
    print(f"   👉 Label Name: {model.config.id2label[pred_id]}")
    print(f"   ℹ️  All Labels: {model.config.id2label}")
else:
    print("   ⚠️ No label names found in config. You need to map 0,1,2 manually.")