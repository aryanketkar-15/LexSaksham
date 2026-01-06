"""
Generate Confusion Matrix and Per-Class Metrics
-----------------------------------------------
Generates confusion matrix visualization and per-class metrics from saved logits and labels.

Saves results to backend/ai_service/results/:
- confusion_matrix.png
- per_class_metrics.json

Usage:
    python generate_confusion_matrix.py --logits ../results/logits.npy --labels ../results/labels.npy --label_classes <path_to_label_classes.json>
"""

import json
import argparse
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, classification_report

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def generate_confusion_matrix(y_true, y_pred, labels_list, output_path):
    """Generate and save confusion matrix as PNG"""
    # Create confusion matrix with all possible labels
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(labels_list))))
    
    # Create figure with better sizing
    fig_size = max(10, len(labels_list) * 0.5)
    plt.figure(figsize=(fig_size, fig_size))
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=labels_list, yticklabels=labels_list,
                cbar_kws={'label': 'Count'})
    plt.title('Confusion Matrix - Clause Classification', fontsize=16, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved confusion matrix to {output_path}")
    plt.close()

def compute_per_class_metrics(y_true, y_pred, labels_list):
    """Compute per-class metrics"""
    per_class_metrics = {}
    
    # Compute metrics for each class
    for idx, label in enumerate(labels_list):
        # Binary classification: this class vs others
        y_true_binary = (y_true == idx).astype(int)
        y_pred_binary = (y_pred == idx).astype(int)
        
        f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
        
        # Support (count of true instances)
        support = np.sum(y_true == idx)
        
        per_class_metrics[label] = {
            "f1": float(f1),
            "precision": float(precision),
            "recall": float(recall),
            "support": int(support)
        }
    
    return per_class_metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logits", type=str, required=True, help="Path to logits numpy file")
    parser.add_argument("--labels", type=str, required=True, help="Path to labels numpy file")
    parser.add_argument("--label_classes", type=str, default="../models/legalbert_clause_classifier/label_classes.json",
                        help="Path to label_classes.json mapping")
    args = parser.parse_args()
    
    # Load logits and labels
    logits_list = np.load(args.logits, allow_pickle=True)
    labels_array = np.load(args.labels, allow_pickle=True)
    
    # Reshape logits if needed
    if isinstance(logits_list, np.ndarray) and logits_list.dtype == object:
        logits_array = np.vstack(logits_list)
    else:
        logits_array = logits_list
        if logits_array.ndim > 2:
            logits_array = logits_array.reshape(logits_array.shape[0], -1)
    
    # Get predictions from logits
    predictions_indices = np.argmax(logits_array, axis=1).flatten()
    
    # Map string labels to indices
    unique_labels = sorted(set(labels_array))
    label_to_index = {label: idx for idx, label in enumerate(unique_labels)}
    labels_indices = np.array([label_to_index[label] for label in labels_array])
    
    # Ensure predictions are valid indices
    predictions_indices = np.array([int(p) if p < len(unique_labels) else 0 for p in predictions_indices])
    
    print(f"Unique labels: {unique_labels}")
    print(f"Number of samples: {len(labels_indices)}")
    print(f"Number of classes: {len(unique_labels)}")
    
    # Generate confusion matrix
    cm_output_path = RESULTS_DIR / "confusion_matrix.png"
    generate_confusion_matrix(labels_indices, predictions_indices, unique_labels, cm_output_path)
    
    # Compute per-class metrics
    per_class_metrics = compute_per_class_metrics(labels_indices, predictions_indices, unique_labels)
    
    # Save per-class metrics
    metrics_output_path = RESULTS_DIR / "per_class_metrics.json"
    with open(metrics_output_path, 'w', encoding='utf-8') as f:
        json.dump(per_class_metrics, f, indent=2)
    print(f"Saved per-class metrics to {metrics_output_path}")
    
    # Print classification report
    print("\n" + "="*100)
    print("CLASSIFICATION REPORT")
    print("="*100)
    print(classification_report(labels_indices, predictions_indices, target_names=unique_labels, zero_division=0))
    
    # Print per-class metrics summary
    print("\n" + "="*100)
    print("PER-CLASS METRICS SUMMARY")
    print("="*100)
    print(f"{'Label':<50} {'F1':<10} {'Precision':<10} {'Recall':<10} {'Support':<10}")
    print("-"*100)
    for label in unique_labels:
        metrics = per_class_metrics[label]
        print(f"{label:<50} {metrics['f1']:<10.4f} {metrics['precision']:<10.4f} {metrics['recall']:<10.4f} {metrics['support']:<10}")
    print("="*100)
    
    # Compute overall metrics
    overall_accuracy = np.mean(labels_indices == predictions_indices)
    overall_f1 = f1_score(labels_indices, predictions_indices, average='macro', zero_division=0)
    
    print(f"\nOverall Accuracy: {overall_accuracy:.4f}")
    print(f"Overall F1 (Macro): {overall_f1:.4f}")

if __name__ == "__main__":
    main()
