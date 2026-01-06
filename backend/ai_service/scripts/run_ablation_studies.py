"""
Ablation Studies Script
-----------------------
Compares classifier performance across different models:
1. LegalBERT (fine-tuned clause classifier)
2. BERT-base (base BERT model)
3. TF-IDF + Logistic Regression (baseline)

Saves results to backend/ai_service/results/ablation_studies.json

Usage:
    python run_ablation_studies.py --test_data <path_to_test_data.jsonl>
"""

import json
import argparse
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_test_data(test_file):
    """Load test data from JSONL file"""
    texts = []
    labels = []
    with open(test_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            texts.append(data.get('text', ''))
            labels.append(data.get('label', ''))
    return texts, labels

def evaluate_model(predictions, labels, model_name):
    """Compute metrics for a model"""
    # Map labels to indices
    unique_labels = sorted(set(labels))
    label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
    label_indices = [label_to_idx[label] for label in labels]
    
    # Map predictions to indices
    pred_indices = [label_to_idx[pred] if pred in label_to_idx else 0 for pred in predictions]
    
    accuracy = accuracy_score(label_indices, pred_indices)
    f1_macro = f1_score(label_indices, pred_indices, average='macro', zero_division=0)
    precision_macro = precision_score(label_indices, pred_indices, average='macro', zero_division=0)
    recall_macro = recall_score(label_indices, pred_indices, average='macro', zero_division=0)
    
    return {
        "model": model_name,
        "accuracy": float(accuracy),
        "f1_macro": float(f1_macro),
        "precision_macro": float(precision_macro),
        "recall_macro": float(recall_macro)
    }

def evaluate_legalbert(texts, labels, model_path):
    """Evaluate LegalBERT clause classifier"""
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        
        predictions = []
        with torch.no_grad():
            for text in texts:
                inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                inputs = {k: v.to(device) for k, v in inputs.items()}
                outputs = model(**inputs)
                logits = outputs.logits
                pred_id = torch.argmax(logits, dim=1).item()
                pred_label = model.config.id2label.get(pred_id, str(pred_id))
                predictions.append(pred_label)
        
        return evaluate_model(predictions, labels, "LegalBERT")
    except Exception as e:
        print(f"Error evaluating LegalBERT: {e}")
        return None

def evaluate_bert_base(texts, labels, model_name="bert-base-uncased"):
    """Evaluate BERT-base model"""
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=len(set(labels)))
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        
        predictions = []
        unique_labels = sorted(set(labels))
        idx_to_label = {idx: label for idx, label in enumerate(unique_labels)}
        
        with torch.no_grad():
            for text in texts:
                inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                inputs = {k: v.to(device) for k, v in inputs.items()}
                outputs = model(**inputs)
                logits = outputs.logits
                pred_id = torch.argmax(logits, dim=1).item()
                pred_label = idx_to_label.get(pred_id, unique_labels[0])
                predictions.append(pred_label)
        
        return evaluate_model(predictions, labels, "BERT-base")
    except Exception as e:
        print(f"Error evaluating BERT-base: {e}")
        return None

def evaluate_tfidf_logreg(texts, labels):
    """Evaluate TF-IDF + Logistic Regression baseline"""
    try:
        vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
        X = vectorizer.fit_transform(texts)
        
        unique_labels = sorted(set(labels))
        label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
        y = [label_to_idx[label] for label in labels]
        
        # Simple train-test split for demonstration
        split_idx = int(0.8 * len(texts))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        lr = LogisticRegression(max_iter=200, random_state=42)
        lr.fit(X_train, y_train)
        
        predictions = lr.predict(X_test)
        pred_labels = [unique_labels[pred] for pred in predictions]
        test_labels = [unique_labels[label] for label in y_test]
        
        return evaluate_model(pred_labels, test_labels, "TF-IDF + LogisticRegression")
    except Exception as e:
        print(f"Error evaluating TF-IDF + LogisticRegression: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_data", type=str, required=True, help="Path to test data file (JSONL format)")
    parser.add_argument("--legalbert_model", type=str, default="../models/legalbert_clause_classifier", 
                        help="Path to LegalBERT model")
    args = parser.parse_args()
    
    # Load test data
    texts, labels = load_test_data(args.test_data)
    print(f"Loaded {len(texts)} test samples")
    
    results = []
    
    # Evaluate LegalBERT
    print("\nEvaluating LegalBERT...")
    legalbert_result = evaluate_legalbert(texts, labels, args.legalbert_model)
    if legalbert_result:
        results.append(legalbert_result)
        print(f"LegalBERT - Accuracy: {legalbert_result['accuracy']:.4f}, F1: {legalbert_result['f1_macro']:.4f}")
    
    # Evaluate BERT-base
    print("\nEvaluating BERT-base...")
    bert_result = evaluate_bert_base(texts, labels)
    if bert_result:
        results.append(bert_result)
        print(f"BERT-base - Accuracy: {bert_result['accuracy']:.4f}, F1: {bert_result['f1_macro']:.4f}")
    
    # Evaluate TF-IDF + LogisticRegression
    print("\nEvaluating TF-IDF + Logistic Regression...")
    tfidf_result = evaluate_tfidf_logreg(texts, labels)
    if tfidf_result:
        results.append(tfidf_result)
        print(f"TF-IDF + LogReg - Accuracy: {tfidf_result['accuracy']:.4f}, F1: {tfidf_result['f1_macro']:.4f}")
    
    # Save results
    out_path = RESULTS_DIR / "ablation_studies.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved ablation study results to {out_path}")
    
    # Print summary table
    print("\n" + "="*70)
    print("ABLATION STUDIES SUMMARY TABLE")
    print("="*70)
    print(f"{'Model':<30} {'Accuracy':<12} {'F1 (Macro)':<12} {'Precision':<12}")
    print("-"*70)
    for result in results:
        print(f"{result['model']:<30} {result['accuracy']:<12.4f} {result['f1_macro']:<12.4f} {result['precision_macro']:<12.4f}")
    print("="*70)

if __name__ == "__main__":
    main()
