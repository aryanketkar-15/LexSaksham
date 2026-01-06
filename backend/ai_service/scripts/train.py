import argparse
import json
import numpy as np
import torch
from pathlib import Path
from datasets import load_dataset
import evaluate  # CHANGED: New library for metrics
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)

# Load metric globally to avoid reloading it every step
accuracy_metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return accuracy_metric.compute(predictions=predictions, references=labels)

def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_file", required=True, help="Path to train_balanced.jsonl")
    parser.add_argument("--validation_file", required=True, help="Path to test_balanced.jsonl")
    parser.add_argument("--output_dir", required=True, help="Where to save the model")
    parser.add_argument("--base_model", default="nlpaueb/legal-bert-base-uncased", help="Base model to fine-tune")
    parser.add_argument("--num_epochs", type=int, default=3)
    parser.add_argument("--per_device_train_batch_size", type=int, default=8)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=1)
    parser.add_argument("--fp16", action="store_true", help="Enable mixed precision training")
    args = parser.parse_args()

    print(f"Loading data from {args.train_file}...")
    
    # Load Datasets
    dataset = load_dataset("json", data_files={"train": args.train_file, "validation": args.validation_file})

    # Determine number of labels from training data
    unique_labels = set(dataset["train"]["label"])
    num_labels = len(unique_labels)
    print(f"Detected {num_labels} unique labels.")

    # Load Tokenizer & Model
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    model = AutoModelForSequenceClassification.from_pretrained(args.base_model, num_labels=num_labels)

    # Tokenization Function
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=256)

    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    # Training Arguments (Optimized for 4060)
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        eval_strategy="epoch",            # Evaluate every epoch
        save_strategy="epoch",            # Save checkpoint every epoch
        learning_rate=2e-5,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_train_epochs=args.num_epochs,
        weight_decay=0.01,
        fp16=args.fp16,                   # Use FP16 for RTX cards
        save_total_limit=2,               # Only keep last 2 checkpoints to save space
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        logging_dir=f"{args.output_dir}/logs",
        logging_steps=50,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )

    print("Starting training...")
    trainer.train()
    
    # Save final model
    trainer.save_model(args.output_dir)
    print(f"Model saved to {args.output_dir}")

if __name__ == "__main__":
    train()