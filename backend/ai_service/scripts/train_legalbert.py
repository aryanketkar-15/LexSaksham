"""
LegalBERT Training (Step G2) — Final Version (GPU Optimized, Debug Logging, DB Safe)
Author: LexSaksham Project
---------------------------------------------------------------
This script loads data from PostgreSQL, fine-tunes LegalBERT,
prints live progress, and saves the trained model & metrics.
"""

import os
import sys
import json
import time
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from datasets import Dataset
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import torch

# Ensure UTF-8 output in Windows terminal
sys.stdout.reconfigure(encoding="utf-8")

def ping(msg: str):
    """Utility: print with timestamp and flush immediately"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()


ping("Starting LegalBERT training script (final GPU version)")

# ---------------------------------------------------------------------
# 1️⃣ Database Configuration
# ---------------------------------------------------------------------
DB_USER = "postgres"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "lexshaksham_db"      # ✅ Final DB name (your setup)
ping("Setting up database connection...")

try:
    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )
    engine = create_engine(connection_url)
    ping("Database engine created successfully.")
except Exception as e:
    print("Failed to create database engine:", e)
    sys.exit(1)


# ---------------------------------------------------------------------
# 2️⃣ Load Data
# ---------------------------------------------------------------------
try:
    ping("Loading clause data from PostgreSQL...")
    query = """
        SELECT clause_text, clause_type
        FROM clauses
        WHERE clause_text IS NOT NULL AND clause_type IS NOT NULL;
    """
    df = pd.read_sql(query, engine)
    ping(f"Loaded {len(df)} clauses from DB.")
except Exception as e:
    print("Database query failed:", e)
    sys.exit(1)


# ---------------------------------------------------------------------
# 3️⃣ Preprocessing & Label Encoding
# ---------------------------------------------------------------------
ping("Cleaning data and encoding labels...")
df = df.dropna(subset=["clause_text", "clause_type"]).drop_duplicates(subset=["clause_text"])
df["clause_text"] = df["clause_text"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
df = df[df["clause_text"].str.len() > 20]

label_encoder = LabelEncoder()
df["label"] = label_encoder.fit_transform(df["clause_type"])
num_labels = len(label_encoder.classes_)
ping(f"Found {num_labels} unique clause types.")

# Save label encoder classes for inference
output_dir = os.path.join(os.path.dirname(__file__), "..", "models", "legalbert_clause")
os.makedirs(output_dir, exist_ok=True)
with open(os.path.join(output_dir, "label_classes.json"), "w", encoding="utf-8") as f:
    json.dump(list(label_encoder.classes_), f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------
# 4️⃣ Split Train/Test
# ---------------------------------------------------------------------
train_df, val_df = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=42)
ping(f"Split complete — Train: {len(train_df)}, Val: {len(val_df)}")

train_ds = Dataset.from_pandas(train_df[["clause_text", "label"]].rename(columns={"clause_text": "text"}))
val_ds = Dataset.from_pandas(val_df[["clause_text", "label"]].rename(columns={"clause_text": "text"}))


# ---------------------------------------------------------------------
# 5️⃣ Tokenizer
# ---------------------------------------------------------------------
MODEL_NAME = "nlpaueb/legal-bert-base-uncased"
ping(f"Loading tokenizer and model: {MODEL_NAME}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)

def tokenize_fn(batch):
    return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=256)

ping("Tokenizing training data...")
train_tok = train_ds.map(tokenize_fn, batched=True)
ping("Tokenizing validation data...")
val_tok = val_ds.map(tokenize_fn, batched=True)

train_tok = train_tok.rename_column("label", "labels")
val_tok = val_tok.rename_column("label", "labels")
train_tok.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
val_tok.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])


# ---------------------------------------------------------------------
# 6️⃣ Model
# ---------------------------------------------------------------------
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=num_labels)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ping(f"Training device detected: {device}")
model.to(device)


# ---------------------------------------------------------------------
# 7️⃣ Training Arguments (GPU Optimized)
# ---------------------------------------------------------------------
train_batch = 16 if torch.cuda.is_available() else 4
eval_batch = 16 if torch.cuda.is_available() else 4
epochs = 4 if torch.cuda.is_available() else 1

ping("Configuring training arguments...")
training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=epochs,
    per_device_train_batch_size=train_batch,
    per_device_eval_batch_size=eval_batch,
    learning_rate=2e-5,
    weight_decay=0.01,
    logging_dir=os.path.join(output_dir, "logs"),
    logging_steps=100,
    save_total_limit=2,
    fp16=torch.cuda.is_available(),  # ✅ Enable half precision on GPU
)


# ---------------------------------------------------------------------
# 8️⃣ Trainer Setup
# ---------------------------------------------------------------------
ping("Initializing Trainer...")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_tok,
    eval_dataset=val_tok,
    tokenizer=tokenizer,
)


# ---------------------------------------------------------------------
# 9️⃣ Train
# ---------------------------------------------------------------------
ping("Starting LegalBERT fine-tuning (GPU accelerated)...")
trainer.train()
ping("Training complete.")


# ---------------------------------------------------------------------
# 🔟 Evaluate
# ---------------------------------------------------------------------
ping("Evaluating model on validation set...")
metrics = trainer.evaluate(eval_dataset=val_tok)
print("Evaluation metrics:", metrics)


# ---------------------------------------------------------------------
# 11️⃣ Save Model, Tokenizer, Labels
# ---------------------------------------------------------------------
ping("Saving model, tokenizer, and label encoder...")
trainer.save_model(output_dir)
tokenizer.save_pretrained(output_dir)

with open(os.path.join(output_dir, "label_encoder.json"), "w", encoding="utf-8") as f:
    json.dump({"classes": list(label_encoder.classes_)}, f, ensure_ascii=False, indent=2)

ping(f"All saved successfully to {output_dir}")
ping("✅ LegalBERT training script finished successfully.")
