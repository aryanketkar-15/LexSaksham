"""
Explainability Utilities — LexSaksham Phase E.4 (Universal Stable Version)
-----------------------------------------------------------------------
Provides SHAP, LIME, and Attention explanations for LegalBERT clause classifier.
✓ Works with CPU/GPU
✓ Clean JSON output for frontend
✓ Fully stable on Python 3.12, NumPy 1.26, modern LIME (master branch)
✓ Handles any tuple shape from LIME without unpack errors
-----------------------------------------------------------------------
"""

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path
import json
from utils.temp_utils import load_temperature


# ============================================================
# 📂 Load model and tokenizer (Lazy on first use)
# ============================================================

CLAUSE_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "legalbert_clause_classifier"

# Module-level globals for lazy loading
_tokenizer = None
_model = None
_num_classes = None
_device = None

def _ensure_models_loaded():
    """Ensure models are loaded (lazy initialization)."""
    global _tokenizer, _model, _num_classes, _device
    if _model is not None:
        return
    _tokenizer = AutoTokenizer.from_pretrained(str(CLAUSE_MODEL_PATH))
    _model = AutoModelForSequenceClassification.from_pretrained(str(CLAUSE_MODEL_PATH))
    _model.eval()
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    _model.to(_device)
    _num_classes = _model.config.num_labels

# Temperature scaling helper
TEMPERATURE_PATH = Path(__file__).resolve().parents[1] / "models" / "temperature.json"

# These were already defined in the old code; keeping for compatibility
tokenizer = None
model = None
num_classes = None
device = None


# ============================================================
# 🔹 Helper — Predict probabilities
# ============================================================

def _predict_proba(texts):
    """Return class probabilities for a list of texts, with temperature scaling."""
    _ensure_models_loaded()
    
    if isinstance(texts, str):
        texts = [texts]
    elif isinstance(texts, list) and isinstance(texts[0], list):
        texts = [t[0] for t in texts]

    inputs = _tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=256)
    inputs = {k: v.to(_model.device) for k, v in inputs.items()}

    T = load_temperature()
    with torch.no_grad():
        logits = _model(**inputs).logits
        scaled_logits = logits / T
        probs = torch.nn.functional.softmax(scaled_logits, dim=-1)

    return probs.cpu().numpy()


# ============================================================
# 🔹 SHAP Explainability (Word Ablation)
# ============================================================
def shap_explain(text: str):
    """Generate SHAP-like importance by measuring confidence drop per word.

    Returns canonical JSON with tokens and importance lists.
    """
    try:
        words = text.split()
        base_probs = _predict_proba([text])[0]
        predicted_class = int(np.argmax(base_probs))
        base_confidence = base_probs[predicted_class]

        importance_scores = []
        for i in range(len(words)):
            modified_text = " ".join(words[:i] + words[i + 1 :])
            if modified_text.strip():
                modified_probs = _predict_proba([modified_text])[0]
                modified_confidence = modified_probs[predicted_class]
                importance = base_confidence - modified_confidence
            else:
                importance = base_confidence
            importance_scores.append(importance)

        _ensure_models_loaded()
        return {
            "model": "legalbert_clause_classifier",
            "predicted_class": predicted_class,
            "class_name": _model.config.id2label.get(predicted_class, f"Class_{predicted_class}"),
            "tokens": words,
            "importance": [float(v) for v in importance_scores],
            "method": "shap",
        }
    except Exception as e:
        print("⚠️ SHAP explanation failed:", e)
        import traceback

        traceback.print_exc()
        return {"error": str(e), "tokens": [], "importance": []}


# ============================================================
# 🔹 Universal LIME Explainability (FINAL, Stable)
# ============================================================
def lime_explain(text: str, num_features: int = 10):
    """Generate token-level importance using LIME (safe for all versions).

    Returns canonical JSON with tokens and importance lists.
    """
    try:
        _ensure_models_loaded()

        def lime_predict_proba(texts):
            if isinstance(texts, str):
                texts = [texts]
            inputs = _tokenizer(
                texts, return_tensors="pt", truncation=True, padding=True, max_length=256
            )
            inputs = {k: v.to(_model.device) for k, v in inputs.items()}
            T = load_temperature()
            with torch.no_grad():
                logits = _model(**inputs).logits
                scaled_logits = logits / T
                probs = torch.nn.functional.softmax(scaled_logits, dim=-1)
            return probs.cpu().numpy()

        probs = lime_predict_proba([text])
        predicted_class = int(np.argmax(probs[0]))
        class_names = list(_model.config.id2label.values())

        # Import LIME lazily so module import doesn't fail when LIME is not installed
        try:
            from lime.lime_text import LimeTextExplainer
        except Exception as e:
            print("⚠️ LIME not available:", e)
            return {"error": "LIME not installed", "explanation": []}

        explainer = LimeTextExplainer(class_names=class_names)
        explanation = explainer.explain_instance(
            text,
            lime_predict_proba,
            num_features=num_features,
            num_samples=500,
        )

        pairs = []

        # ---- Step 1: Try as_list() ----
        try:
            exp_list = explanation.as_list(label=predicted_class)
            for entry in exp_list:
                if isinstance(entry, (list, tuple)):
                    word = str(entry[0])
                    weight = float(entry[1]) if len(entry) > 1 else 0.0
                    pairs.append((word, weight))
        except Exception as e:
            print("⚠️ LIME as_list() failed, trying fallback:", e)

        # ---- Step 2: Fallback to as_map() ----
        if not pairs:
            exp_map = explanation.as_map()
            label_to_use = predicted_class if predicted_class in exp_map else list(exp_map.keys())[0]
            raw_entries = exp_map[label_to_use]

            feature_names = getattr(explanation.domain_mapper.indexed_string, "as_list", None)
            if callable(feature_names):
                feature_names = feature_names()
            elif isinstance(feature_names, list):
                feature_names = feature_names
            else:
                feature_names = []

            # ✅ FINAL ultra-safe parser
            for entry in raw_entries:
                # Sometimes nested like [[(fid, weight)]]
                if isinstance(entry, list) and len(entry) == 1 and isinstance(entry[0], (list, tuple)):
                    entry = entry[0]

                if not isinstance(entry, (list, tuple)) or not entry:
                    continue

                try:
                    flat = []
                    for x in entry:
                        if isinstance(x, (list, tuple)):
                            flat.extend(x)
                        else:
                            flat.append(x)

                    feature_id = int(flat[0])
                    weight = float(flat[-1])

                    if 0 <= feature_id < len(feature_names):
                        word = str(feature_names[feature_id])
                        pairs.append((word, weight))
                except Exception as inner_e:
                    print("⚠️ Skipped malformed LIME entry:", entry, inner_e)
                    continue

        tokens = [w for w, _ in pairs]
        importance = [float(wt) for _, wt in pairs]

        return {
            "model": "legalbert_clause_classifier",
            "predicted_class": predicted_class,
            "class_name": class_names[predicted_class] if predicted_class < len(class_names) else f"Class_{predicted_class}",
            "tokens": tokens,
            "importance": importance,
            "method": "lime",
        }

    except Exception as e:
        print("⚠️ LIME explanation failed (final catch):", e)
        import traceback

        traceback.print_exc()
        return {"error": str(e), "explanation": []}


# ============================================================
# 🔹 Attention-based Explainability
# ============================================================

def attention_explain(text: str):
    """Explainability using model attention weights, with temperature scaling."""
    try:
        _ensure_models_loaded()
        inputs = _tokenizer(
            text, return_tensors="pt", truncation=True, padding=True, max_length=256
        )
        inputs = {k: v.to(_model.device) for k, v in inputs.items()}

        T = load_temperature()
        with torch.no_grad():
            outputs = _model(**inputs, output_attentions=True)
            logits = outputs.logits
            attentions = outputs.attentions
            scaled_logits = logits / T
            probs = torch.nn.functional.softmax(scaled_logits, dim=-1)

        predicted_class = int(torch.argmax(probs[0]))
        avg_attention = torch.stack(attentions).mean(dim=[0, 1, 2])
        importance = avg_attention[0, 1:].cpu().numpy()

        tokens = _tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        tokens = [t for t in tokens[1:] if t not in ["[SEP]", "[PAD]", "[CLS]"]]

        min_len = min(len(tokens), len(importance))

        return {
            "model": "legalbert_clause_classifier",
            "predicted_class": predicted_class,
            "class_name": _model.config.id2label.get(predicted_class, f"Class_{predicted_class}"),
            "tokens": tokens[:min_len],
            "importance": [float(v) for v in importance[:min_len]],
            "method": "attention",
        }

    except Exception as e:
        print("⚠️ Attention explanation failed:", e)
        import traceback

        traceback.print_exc()
        return {"error": str(e), "tokens": [], "importance": []}


# ============================================================
# 🧪 Quick Test (optional standalone run)
# ============================================================
if __name__ == "__main__":
    sample = "The party shall indemnify the client for any damages arising from negligence."
    print("\n--- LIME ---")
    print(lime_explain(sample))
    print("\n--- SHAP ---")
    print(shap_explain(sample))
    print("\n--- Attention ---")
    print(attention_explain(sample))
