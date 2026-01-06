# backend/ai_service/scripts/train_classifier_weighted.py
import json
import torch
import numpy as np
from pathlib import Path
from transformers import BertTokenizerFast, BertForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset

# Paths (adjust if needed)
TRAIN_FILE = "backend/ai_service/datasets/clause_dataset/prepared/train_int.jsonl"
VAL_FILE = "backend/ai_service/datasets/clause_dataset/prepared/validation_int.jsonl"
MODEL_PATH = "backend/ai_service/models/legalbert_clause_classifier"
WEIGHTS_FILE = "backend/ai_service/results/class_weights.json"
OUTPUT = "backend/ai_service/models/legalbert_clause_classifier_retrained"

# Hyperparams tuned for RTX 4060 (8GB)
PER_DEVICE_BATCH = 4                # try 4 for 8GB VRAM
GRAD_ACCUM_STEPS = 4                # effective batch = 4 * 4 = 16
MAX_LEN = 256
NUM_EPOCHS = 3                    # change to 1 for a quick smoke-test
LR = 3e-5

print("Loading tokenizer and base model from", MODEL_PATH)
tokenizer = BertTokenizerFast.from_pretrained(MODEL_PATH)
model = BertForSequenceClassification.from_pretrained(MODEL_PATH)

print("Loading datasets...")
dataset = load_dataset("json", data_files={
    "train": TRAIN_FILE,
    "validation": VAL_FILE
})

def preprocess(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=MAX_LEN)

dataset = dataset.map(preprocess, batched=True, remove_columns=[c for c in dataset["train"].column_names if c not in ("text","label")])

# Load raw class weights (numeric keys -> float)
raw_weights = json.load(open(WEIGHTS_FILE))
# Convert keys to ints and make ordered list 0..num_labels-1
num_labels = model.config.num_labels
weights_arr = np.array([float(raw_weights.get(str(i), 1.0)) for i in range(num_labels)], dtype=np.float64)

print("Raw class weights:", dict(enumerate(weights_arr.tolist())))

# Smoothing: sqrt, clip, then normalize to mean=1.0
smoothed = np.sqrt(weights_arr)
min_cap = 0.2
max_cap = 10.0
smoothed = np.clip(smoothed, min_cap, max_cap)
smoothed = smoothed / smoothed.mean()  # normalize so avg weight == 1.0

print("Smoothed/clipped class weights (will be used):")
print({i: float(smoothed[i]) for i in range(len(smoothed))})

weights_tensor = torch.tensor(smoothed, dtype=torch.float)

# Weighted Trainer subclass
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        loss_fct = torch.nn.CrossEntropyLoss(weight=weights_tensor.to(model.device))
        loss = loss_fct(logits, labels)
        return (loss, outputs) if return_outputs else loss

training_args = TrainingArguments(
    output_dir=OUTPUT,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=PER_DEVICE_BATCH,
    per_device_eval_batch_size=PER_DEVICE_BATCH,
    gradient_accumulation_steps=GRAD_ACCUM_STEPS,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=LR,
    fp16=True,                    # mixed precision - helps on 8GB
    logging_steps=200,
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
)

trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"]
)

if __name__ == "__main__":
    trainer.train()
    trainer.save_model(OUTPUT)
    print("Training complete. Model saved to:", OUTPUT)
