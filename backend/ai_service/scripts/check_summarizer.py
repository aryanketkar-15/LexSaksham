from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os

# CONFIGURATION
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "legal_t5_summarizer")

print(f"📂 Loading T5 Summarizer from: {MODEL_PATH}")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
    print("✅ T5 Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading T5 Model: {e}")
    exit()

# TEST DATA
complex_clause = """
In the event that the Service Provider fails to perform the Services in accordance with the specifications 
set forth in Exhibit A, the Client shall have the right to terminate this Agreement immediately upon written notice, 
without prejudice to any other rights or remedies available at law or in equity, and the Service Provider shall 
refund any and all fees paid by the Client for such non-conforming Services.
"""

print("\n📜 Original Text:")
print(complex_clause.strip())

# GENERATE SUMMARY
print("\n🤖 Generating Summary...")
inputs = tokenizer.encode("summarize: " + complex_clause, return_tensors="pt", max_length=512, truncation=True)
outputs = model.generate(inputs, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(f"\n✨ AI Summary:\n{summary}")