import torch
import json
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path

class ClauseClassifier:
    def __init__(self, model_path="backend/ai_service/models/legalbert_balanced", label_map_path="backend/ai_service/datasets/label_map.json"):
        # Check if paths exist
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model not found at {model_path}. Did you train it?")
        if not Path(label_map_path).exists():
            raise FileNotFoundError(f"Label map not found at {label_map_path}. Did you balance the dataset?")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading model from {model_path} on {self.device}...")
        
        # Load Model & Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()

        # Load Label Map (ID -> Text)
        with open(label_map_path, 'r') as f:
            self.label_map = json.load(f)
        # Reverse map: {0: "Confidentiality"} (Ensure keys are integers)
        self.id2label = {int(v): k for k, v in self.label_map.items()}

    def predict(self, text):
        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=256)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Get Probabilities
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        confidence, predicted_id = torch.max(probs, dim=-1)

        predicted_class = self.id2label[predicted_id.item()]
        confidence_score = confidence.item()

        return {
            "label": predicted_class,
            "confidence": round(confidence_score, 4),
            "flag_for_review": confidence_score < 0.60  # Flag if confidence is low
        }

# Test block - This runs only when you execute this file directly
if __name__ == "__main__":
    try:
        classifier = ClauseClassifier()
        # Test with a dummy sentence
        test_text = "The Service Provider shall indemnify and hold harmless the Client against any claims."
        print("\nTest Prediction:")
        print(json.dumps(classifier.predict(test_text), indent=2))
    except Exception as e:
        print(f"\nError: {e}")