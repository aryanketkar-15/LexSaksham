from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "legal_t5_summarizer")

print(f"Loading T5 from: {MODEL_PATH}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)

text = """
In the event that the Service Provider fails to perform the Services in accordance with the specifications 
set forth in Exhibit A, the Client shall have the right to terminate this Agreement immediately upon written notice, 
without prejudice to any other rights or remedies available at law or in equity, and the Service Provider shall 
refund any and all fees paid by the Client for such non-conforming Services.
"""

input_ids = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=512, truncation=True)

# --- THE FIX: BETTER PARAMETERS ---
outputs = model.generate(
    input_ids, 
    max_length=120, 
    min_length=30, 
    length_penalty=1.0, 
    num_beams=6,              # More beams = smarter search
    no_repeat_ngram_size=3,   # CRITICAL: Banned repeating 3-word phrases
    repetition_penalty=2.5,   # CRITICAL: Penalize using the same words again
    early_stopping=True
)

summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("\n--- IMPROVED SUMMARY ---")
print(summary)