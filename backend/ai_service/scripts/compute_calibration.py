"""
Compute Expected Calibration Error (ECE)
---------------------------------------
Computes ECE before and after temperature scaling for a classifier.
Saves results to backend/ai_service/results/calibration.json

Usage:
    python backend/ai_service/scripts/compute_calibration.py --logits <path_to_logits.npy> --labels <path_to_labels.npy> --temperature <float>
"""

import json
import argparse
import numpy as np
from pathlib import Path
from sklearn.calibration import calibration_curve

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def compute_ece(probabilities, labels, n_bins=10):
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_edges[:-1]
    bin_uppers = bin_edges[1:]

    ece = 0.0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (probabilities > bin_lower) & (probabilities <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            avg_confidence = np.mean(probabilities[in_bin])
            avg_accuracy = np.mean(labels[in_bin])
            ece += np.abs(avg_confidence - avg_accuracy) * prop_in_bin

    return ece

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logits", type=str, required=True, help="Path to logits file (NumPy .npy format)")
    parser.add_argument("--labels", type=str, required=True, help="Path to labels file (NumPy .npy format)")
    parser.add_argument("--temperature", type=float, default=1.0, help="Temperature scaling factor")
    args = parser.parse_args()

    logits = np.load(args.logits)
    labels = np.load(args.labels)

    # Reshape logits if needed (remove extra dimensions)
    if logits.ndim > 2:
        logits = logits.reshape(logits.shape[0], -1)

    # Map string labels to integers
    unique_labels = np.unique(labels)
    label_to_index = {label: idx for idx, label in enumerate(unique_labels)}
    labels = np.array([label_to_index[label] for label in labels], dtype=int)

    # Apply temperature scaling
    scaled_logits = logits / args.temperature
    probabilities = np.exp(scaled_logits) / np.sum(np.exp(scaled_logits), axis=1, keepdims=True)
    predicted_labels = np.argmax(probabilities, axis=1)

    # Compute ECE using true class probabilities
    true_class_probs = probabilities[np.arange(len(labels)), labels]
    ece = compute_ece(true_class_probs, (predicted_labels == labels).astype(int))

    results = {
        "temperature": args.temperature,
        "ece": ece
    }

    out_path = RESULTS_DIR / "calibration.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved calibration results to {out_path}")

if __name__ == "__main__":
    main()