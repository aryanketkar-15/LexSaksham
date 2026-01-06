"""
Temperature Scaling Calibration Script for LegalBERT Clause Classifier

Purpose: Optimize a scalar temperature T to improve numeric calibration of model confidence.
After calibration, logits are divided by T before softmax to reduce over/under-confidence.

Usage:
    python calibrate_temperature.py \\
        --valset /path/to/val.jsonl \\
        --out /path/to/temperature.json \\
        --device cuda
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_model_and_tokenizer(model_dir: str, device: str):
    """Load clause classifier model and tokenizer."""
    logger.info(f"Loading model from {model_dir}...")
    # Support both local filesystem paths and HF repo IDs. For local paths, resolve
    # to absolute path and load with local_files_only=True to avoid HF repo id validation.
    try:
        p = Path(model_dir)
        if p.exists():
            model_path = str(p.resolve())
            tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)
        else:
            # Might be a HF repo id (namespace/repo) or shortcut
            tokenizer = AutoTokenizer.from_pretrained(model_dir)
            model = AutoModelForSequenceClassification.from_pretrained(model_dir)

        # Normalize device to a torch.device
        if isinstance(device, str):
            device_t = torch.device(device)
        else:
            device_t = device

        model = model.to(device_t)
        model.eval()
        logger.info("Model loaded successfully.")
        return tokenizer, model, device_t
    except Exception as e:
        logger.error(f"Failed to load model/tokenizer from {model_dir}: {e}")
        raise


def load_validation_set(valset_path: str) -> list:
    """
    Load validation set from JSONL.

    Expected format per line: {"text": "...", "label": "LABEL_X"} or {"text": "...", "label_idx": 3}
    """
    examples = []
    try:
        with open(valset_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    text = data.get("text", "")
                    label = data.get("label")
                    label_idx = data.get("label_idx")

                    if not text:
                        logger.warning(f"Line {line_num}: missing 'text'")
                        continue

                    # Try to extract label index
                    if isinstance(label, str) and label.startswith("LABEL_"):
                        label_idx = int(label.split("_")[1])
                    elif isinstance(label_idx, int):
                        pass
                    else:
                        logger.warning(f"Line {line_num}: invalid label format. Expected LABEL_X or label_idx.")
                        continue

                    examples.append({"text": text, "label_idx": label_idx})
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Line {line_num}: {e}")
                    continue

        logger.info(f"Loaded {len(examples)} validation examples from {valset_path}")
        return examples
    except FileNotFoundError:
        logger.error(f"Validation set not found: {valset_path}")
        sys.exit(1)


def collect_logits_and_labels(examples: list, tokenizer, model, device: str, max_length: int = 256):
    """
    Collect model logits and true labels for all examples.

    Returns:
        logits_list: list of numpy arrays (num_examples, num_classes)
        labels_list: list of true label indices
    """
    logits_list = []
    labels_list = []

    logger.info("Collecting logits from model...")
    with torch.no_grad():
        for i, example in enumerate(examples):
            if (i + 1) % 100 == 0:
                logger.info(f"  Processed {i + 1}/{len(examples)}")

            text = example["text"]
            label_idx = example["label_idx"]

            # Tokenize
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=max_length
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Forward pass
            outputs = model(**inputs)
            logits = outputs.logits.cpu().numpy()  # shape: (1, num_classes)

            logits_list.append(logits[0])  # Remove batch dimension
            labels_list.append(label_idx)

    logger.info(f"Collected logits for {len(logits_list)} examples")
    return np.array(logits_list), np.array(labels_list)


def compute_temperature(logits: np.ndarray, labels: np.ndarray, num_iterations: int = 100) -> float:
    """
    Find optimal temperature T by minimizing NLL on validation set.

    Uses scipy.optimize.minimize on a simple scalar optimization.

    Args:
        logits: shape (num_examples, num_classes)
        labels: shape (num_examples,) with true label indices

    Returns:
        Optimal temperature T > 0
    """
    from scipy.optimize import minimize_scalar

    def nll_loss(T: float) -> float:
        """Negative log-likelihood with temperature scaling."""
        if T <= 0:
            return 1e10

        # Scale logits by temperature
        scaled_logits = logits / T
        # Compute softmax probabilities
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

        # NLL: -log(p_true_class)
        nll = -np.log(probs[np.arange(len(labels)), labels] + 1e-10)
        return np.mean(nll)

    logger.info("Optimizing temperature T...")
    result = minimize_scalar(nll_loss, bounds=(0.1, 5.0), method="bounded")

    T_opt = result.x
    loss_opt = result.fun

    logger.info(f"Optimal temperature T = {T_opt:.4f}, NLL = {loss_opt:.4f}")
    return T_opt


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate temperature scaling for LegalBERT clause classifier."
    )
    parser.add_argument(
        "--valset",
        type=str,
        required=True,
        help="Path to validation set JSONL (expected: {text, label|label_idx})"
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output path for temperature.json"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="./models/legalbert_clause_classifier",
        help="Path to clause classifier model"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device: cuda or cpu"
    )

    args = parser.parse_args()

    # Load model
    tokenizer, model, device = load_model_and_tokenizer(args.model, args.device)

    # Load validation set
    examples = load_validation_set(args.valset)
    if not examples:
        logger.error("No valid examples in validation set.")
        sys.exit(1)

    # Collect logits
    logits, labels = collect_logits_and_labels(examples, tokenizer, model, device)

    # Compute temperature
    T_opt = compute_temperature(logits, labels)

    # Save result
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = {"temperature": float(T_opt)}
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Temperature saved to {output_path}")
    logger.info(f"Result: {result}")

    # Sanity check: compute NLL before/after
    from scipy.special import softmax as scipy_softmax

    nll_before = -np.log(scipy_softmax(logits, axis=1)[np.arange(len(labels)), labels] + 1e-10).mean()
    nll_after = -np.log(scipy_softmax(logits / T_opt, axis=1)[np.arange(len(labels)), labels] + 1e-10).mean()

    logger.info(f"NLL before calibration: {nll_before:.4f}")
    logger.info(f"NLL after calibration:  {nll_after:.4f}")
    logger.info(f"Improvement: {(nll_before - nll_after) / nll_before * 100:.1f}%")


if __name__ == "__main__":
    main()
