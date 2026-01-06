# train_classifier_focal.py
"""
Training script that uses focal loss (optionally with per-class alpha from class_weights)
Usage example (see README below):
python backend/ai_service/scripts/train_classifier_focal.py \
  --train_file backend/ai_service/datasets/clause_dataset/prepared/train_relabelled.jsonl \
  --validation_file backend/ai_service/datasets/clause_dataset/prepared/validation_int.jsonl \
  --model_dir backend/ai_service/models/legalbert_clause_classifier \
  --output_dir backend/ai_service/models/legalbert_clause_classifier_focal \
  --num_labels 25 \
  --epochs 3 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 2 \
  --learning_rate 2e-5 \
  --fp16 \
  --class_weights backend/ai_service/results/class_weights.json \
  --gamma 2.0
"""
import argparse
import json
import math
from pathlib import Path
import torch
import torch.nn.functional as F
from torch import nn
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from datasets import load_dataset

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--train_file", required=True)
    p.add_argument("--validation_file", required=True)
    p.add_argument("--model_dir", required=True)
    p.add_argument("--output_dir", required=True)
    p.add_argument("--num_labels", type=int, default=25)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--per_device_train_batch_size", type=int, default=8)
    p.add_argument("--gradient_accumulation_steps", type=int, default=1)
    p.add_argument("--learning_rate", type=float, default=2e-5)
    p.add_argument("--max_length", type=int, default=256)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--class_weights", default=None, help="path to class_weights.json (optional)")
    p.add_argument("--gamma", type=float, default=2.0, help="focal loss gamma")
    p.add_argument("--alpha", default=None, help="optional alpha (float) or path to json mapping of per-class alphas")
    return p.parse_args()

class FocalTrainer(Trainer):
    def __init__(self, gamma=2.0, alpha=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gamma = gamma
        # alpha: None, float, or tensor shape (num_labels,)
        if alpha is not None:
            if isinstance(alpha, (list, tuple)):
                self.alpha = torch.tensor(alpha, dtype=torch.float)
            elif isinstance(alpha, float) or isinstance(alpha, int):
                self.alpha = torch.tensor([float(alpha)])
            elif isinstance(alpha, dict):
                # assume keys are label indices as strings
                al = [0.0] * self.args.label_names_len if hasattr(self.args, "label_names_len") else None
                # fallback: create vector of length model.config.num_labels
                nl = self.model.config.num_labels
                vec = [0.0] * nl
                for k, v in alpha.items():
                    vec[int(k)] = float(v)
                self.alpha = torch.tensor(vec, dtype=torch.float)
            else:
                self.alpha = None
        else:
            self.alpha = None

    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get("labels")
        # move labels to device
        outputs = model(**inputs)
        logits = outputs.logits  # (batch, num_labels)
        # compute focal loss
        ce_loss = F.cross_entropy(logits, labels, reduction='none')  # per sample
        probs = F.softmax(logits, dim=-1)
        # p_t = prob of the true class for each sample
        idx = labels.view(-1, 1)
        p_t = probs.gather(1, idx).squeeze(1).clamp(min=1e-8)
        mod_factor = (1.0 - p_t) ** self.gamma
        loss = mod_factor * ce_loss  # (batch,)
        # apply alpha if provided: alpha per-class or scalar
        if self.alpha is not None:
            if self.alpha.ndim == 1 and self.alpha.shape[0] == logits.shape[-1]:
                # per-class
                a = self.alpha.to(logits.device)[labels]
            else:
                a = self.alpha.to(logits.device).view(1).expand_as(loss)
            loss = a * loss
        loss = loss.mean()
        return (loss, outputs) if return_outputs else loss

def main():
    args = parse_args()
    # tokenizer + model
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_dir, num_labels=args.num_labels
    )

    # load datasets (expects jsonl with {"text":..., "label": INT})
    ds = load_dataset("json", data_files={"train": args.train_file, "validation": args.validation_file})
    def preprocess(example):
        toks = tokenizer(example["text"], truncation=True, max_length=args.max_length)
        toks["labels"] = int(example["label"])
        return toks

    ds = ds.map(preprocess, batched=False, remove_columns=ds["train"].column_names)
    ds["train"].set_format(type="torch")
    ds["validation"].set_format(type="torch")

    # alpha: load class_weights if provided (we'll normalize to reasonable scale)
    alpha = None
    if args.class_weights:
        cw = json.load(open(args.class_weights))
        # cw may map str indices to weight (bigger weight for minority). For focal alpha we'd like smaller alpha for majority?
        # We will normalize class weights to sum 1 and use as alpha.
        # Convert to list in label-index order
        nl = args.num_labels
        vec = [float(cw.get(str(i), 0.0)) for i in range(nl)]
        s = sum(vec)
        if s == 0:
            alpha = None
        else:
            alpha = [v / s for v in vec]
    elif args.alpha:
        try:
            f = float(args.alpha)
            alpha = float(f)
        except Exception:
            alpha = json.load(open(args.alpha))

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=200,
        save_total_limit=3,
        learning_rate=args.learning_rate,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        fp16=args.fp16,
        seed=args.seed,
        report_to="none"
    )

    # attach a small helper so FocalTrainer can see label vector size if needed
    training_args.label_names_len = args.num_labels

    trainer = FocalTrainer(
        gamma=args.gamma,
        alpha=alpha,
        model=model,
        args=training_args,
        train_dataset=ds["train"],
        eval_dataset=ds["validation"],
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model(args.output_dir)
    print("Training finished. Saved to:", args.output_dir)

if __name__ == "__main__":
    main()
