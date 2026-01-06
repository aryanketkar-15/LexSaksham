import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM
from sklearn.metrics import classification_report, accuracy_score
from rouge_score import rouge_scorer
import os
import numpy as np

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_PATH = os.path.join(MODELS_DIR, "prepared_data.csv")

BERT_PATH = os.path.join(MODELS_DIR, "legalbert_clause_classifier")
T5_PATH = os.path.join(MODELS_DIR, "legal_t5_summarizer")

# --- 1. EVALUATE CLASSIFIER (BERT) ---
def evaluate_classifier():
    print("\n📊 --- EVALUATING LEGALBERT CLASSIFIER ---")
    if not os.path.exists(DATA_PATH):
        print("❌ Data file not found. Cannot evaluate.")
        return

    try:
        # Load FULL dataset first to establish correct label mapping
        full_df = pd.read_csv(DATA_PATH)
        # Verify column exists
        label_col = 'clause_type' 
        if label_col not in full_df.columns:
            print(f"❌ Column '{label_col}' not found in CSV.")
            return

        # Take a sample for testing (or use full_df for complete accuracy)
        # Using 200 samples for better statistical significance
        test_df = full_df.sample(n=200, random_state=42) 
        print(f"Loaded {len(test_df)} test samples (from {len(full_df)} total records).")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return

    try:
        tokenizer = AutoTokenizer.from_pretrained(BERT_PATH)
        model = AutoModelForSequenceClassification.from_pretrained(BERT_PATH)
    except Exception as e:
        print(f"❌ Could not load BERT model: {e}")
        return

    # Get true labels for the test set
    y_true = test_df[label_col].astype(str).tolist()
    
    # Predict
    y_pred = []
    print("Running predictions...")
    
    # --- CRITICAL FIX: BUILD LABEL MAP FROM FULL DATASET ---
    # We must sort the UNIQUE labels from the FULL dataset, not just the sample.
    # This ensures ID 0 is always the same class (e.g., "Arbitration") regardless of sample.
    unique_labels = sorted(full_df[label_col].dropna().unique().tolist())
    id2label = {i: label for i, label in enumerate(unique_labels)}
    
    print(f"ℹ️ Reconstructed Label Map with {len(id2label)} classes (from full data).")
    
    for text in test_df['clause_text']:
        inputs = tokenizer(str(text), return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = model(**inputs).logits
        pred_id = torch.argmax(logits, dim=1).item()
        
        # Map ID back to Label using our robust map
        pred_label = id2label.get(pred_id, "Unknown")
        y_pred.append(pred_label)

    # Metrics
    accuracy = accuracy_score(y_true, y_pred)
    print(f"\n✅ Accuracy: {accuracy*100:.2f}%")
    print("\nDetailed Report:")
    # zero_division=0 prevents warnings for classes not predicted
    print(classification_report(y_true, y_pred, zero_division=0))

# --- 2. EVALUATE SUMMARIZER (T5) ---
def evaluate_summarizer():
    print("\n📝 --- EVALUATING T5 SUMMARIZER ---")
    
    test_text = "The Service Provider shall indemnify and hold harmless the Client against all claims, losses, damages, and expenses."
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(T5_PATH)
        model = AutoModelForSeq2SeqLM.from_pretrained(T5_PATH)
    except Exception as e:
        print(f"❌ Could not load T5 model: {e}")
        return

    inputs = tokenizer.encode("summarize: " + test_text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(inputs, max_length=150, num_beams=4, early_stopping=True)
    generated_summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    print(f"\nInput: {test_text}")
    print(f"Generated: {generated_summary}")
    
    # Example ROUGE calculation (Needs a reference summary to be real)
    reference = "The Provider must pay for the Client's losses."
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, generated_summary)
    
    print("\nDummy ROUGE Scores (against a fake reference):")
    print(f"ROUGE-1: {scores['rouge1'].fmeasure:.4f}")
    print(f"ROUGE-L: {scores['rougeL'].fmeasure:.4f}")

if __name__ == "__main__":
    evaluate_classifier()
    evaluate_summarizer()