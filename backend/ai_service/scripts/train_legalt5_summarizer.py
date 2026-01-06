"""
train_legalt5_summarizer.py
-------------------------------------------------
Fine-tune a T5 model to convert legal clauses into
plain-language summaries (balanced formal + simple).
GPU optimized — runs with CUDA + FP16 if available.
Safe evaluation (no OverflowError).
-------------------------------------------------
"""

import os, re, datetime, torch, inspect
from pathlib import Path
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments
)
import evaluate

# ============================================================
# 📂 CONFIGURATION
# ============================================================
BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "datasets" / "clause_dataset" / "prepared"
TRAIN_FILE = str(DATA_DIR / "summarize_train.jsonl")
VAL_FILE   = str(DATA_DIR / "summarize_validation.jsonl")

OUT_DIR = BASE / "models" / "legal_t5_summarizer"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "t5-base"   # Alternatives: "t5-small", "google/pegasus-xsum"
MAX_INPUT_LENGTH = 256
MAX_TARGET_LENGTH = 64
EPOCHS = 4
LR = 3e-5

device = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 8 if device == "cuda" else 4

print("="*70)
print(f" LexSaksham Summarizer Training — Device: {device.upper()}")
print("="*70)

# ============================================================
# 🧾 LOGGING
# ============================================================
ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
print(f"Training started: {ts}")

# ============================================================
# 📦 LOAD DATASET
# ============================================================
data_files = {}
if Path(TRAIN_FILE).exists(): data_files["train"] = TRAIN_FILE
if Path(VAL_FILE).exists(): data_files["validation"] = VAL_FILE
if not data_files:
    raise SystemExit(" summarize_train.jsonl / summarize_validation.jsonl not found in prepared/")

dataset = load_dataset("json", data_files=data_files)
print(" Loaded dataset splits:", list(dataset.keys()))
if "train" in dataset:
    print(" Train records:", len(dataset["train"]))
if "validation" in dataset:
    print(" Validation records:", len(dataset["validation"]))

# ============================================================
# 🔤 TOKENIZATION & PREPROCESSING
# ============================================================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)

def clean_text(s: str):
    if not s: return ""
    s = re.sub(r"\s+", " ", s).strip()
    return s

def preprocess(example):
    src = clean_text(example["text"])
    tgt = clean_text(example.get("summary", ""))
    model_inputs = tokenizer(src, max_length=MAX_INPUT_LENGTH, truncation=True)
    labels = tokenizer(text_target=tgt, max_length=MAX_TARGET_LENGTH, truncation=True)
    # Replace pad token IDs with -100 for loss masking
    model_inputs["labels"] = [
        (lid if lid != tokenizer.pad_token_id else -100) for lid in labels["input_ids"]
    ]
    return model_inputs

tokenized = dataset.map(preprocess, batched=False)
if "train" in tokenized:
    tokenized = tokenized.remove_columns([
        c for c in tokenized["train"].column_names
        if c not in ["input_ids", "attention_mask", "labels"]
    ])
print(" Tokenized sizes:")
for split in ["train", "validation"]:
    if split in tokenized:
        try:
            print(f"  {split}:", len(tokenized[split]))
        except Exception:
            pass

# ============================================================
# 🧠 MODEL INITIALIZATION (GPU ENFORCED)
# ============================================================
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
print(f" Model loaded on {device.upper()}")

data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

# ============================================================
# ⚙️ TRAINING ARGUMENTS (VERSION-SAFE)
# ============================================================
args = inspect.signature(Seq2SeqTrainingArguments.__init__).parameters
if "evaluation_strategy" in args:
    eval_key = "evaluation_strategy"
elif "eval_strategy" in args:
    eval_key = "eval_strategy"
else:
    eval_key = None

common_kwargs = dict(
    output_dir=str(OUT_DIR),
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    predict_with_generate=True,
    learning_rate=LR,
    num_train_epochs=EPOCHS,
    weight_decay=0.01,
    save_total_limit=2,
    logging_dir=str(OUT_DIR / "logs"),
    fp16=True if device == "cuda" else False,   # ✅ enable mixed precision
    generation_max_length=MAX_TARGET_LENGTH,
    load_best_model_at_end=True if "validation" in tokenized else False,
    report_to="none"  # disable wandb/mlflow noise
)

if eval_key:
    common_kwargs[eval_key] = "epoch" if "validation" in tokenized else "no"
    common_kwargs["save_strategy"] = "epoch" if "validation" in tokenized else "no"
else:
    common_kwargs["save_strategy"] = "no"

# Stable generation and model selection
common_kwargs["generation_num_beams"] = 4
common_kwargs["metric_for_best_model"] = "rougeL"
common_kwargs["greater_is_better"] = True
common_kwargs["seed"] = 42
common_kwargs["logging_strategy"] = "steps"
common_kwargs["logging_steps"] = 100
common_kwargs["disable_tqdm"] = False

training_args = Seq2SeqTrainingArguments(**common_kwargs)
print(f" TrainingArguments initialized with {eval_key or 'no-eval'} mode")

# ============================================================
# 📊 METRICS (ROUGE) — SAFE EVALUATION
# ============================================================
rouge = evaluate.load("rouge")

def compute_metrics(eval_pred):
    preds, labels = eval_pred

    # Handle tuple predictions
    if isinstance(preds, tuple):
        preds = preds[0]

    # Ensure integer tokens and restore ignored labels
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    preds = [[(int(p) if int(p) >= 0 else pad_id) for p in pred] for pred in preds]
    labels = [[(int(l) if int(l) != -100 else pad_id) for l in lab] for lab in labels]

    # Decode safely
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    decoded_preds = [p.strip() for p in decoded_preds]
    decoded_labels = [l.strip() for l in decoded_labels]

    result = rouge.compute(predictions=decoded_preds, references=decoded_labels, use_stemmer=True)
    return {k: round(v, 4) for k, v in result.items()}

# ============================================================
# 🚀 TRAINER
# ============================================================
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized.get("train"),
    eval_dataset=tokenized.get("validation"),
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics if "validation" in tokenized else None,
)

# ============================================================
# 🏋️‍♂️ TRAIN & SAVE
# ============================================================
trainer.train()
trainer.save_model(str(OUT_DIR))
tokenizer.save_pretrained(str(OUT_DIR))
print("\n Training complete. Model saved to:", OUT_DIR)
print(" GPU was used:", torch.cuda.is_available())
