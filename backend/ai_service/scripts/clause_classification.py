import psycopg2
import pandas as pd
from datasets import Dataset
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
import torch
import os

# --------------------------
# 1️⃣ PostgreSQL connection
# --------------------------
conn = psycopg2.connect(
    dbname="lexshaksham_db",
    user="postgres",          # Replace with your DB username
    password="root",  # Replace with your DB password
    host="localhost",          # Change if using remote DB
    port="5432"
)

# Fetch clauses with labels
query = "SELECT clause_id, clause_text, clause_type FROM clauses WHERE clause_type IS NOT NULL;"
df = pd.read_sql(query, conn)

if df.empty:
    raise ValueError("No labeled clauses found in clause_type column for training.")

# Map clause_type to numeric labels
labels = {label: idx for idx, label in enumerate(df['clause_type'].unique())}
df['label'] = df['clause_type'].map(labels)

# --------------------------
# 2️⃣ Split dataset
# --------------------------
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df['clause_text'].tolist(),
    df['label'].tolist(),
    test_size=0.1,
    random_state=42
)

train_dataset = Dataset.from_dict({'text': train_texts, 'label': train_labels})
val_dataset = Dataset.from_dict({'text': val_texts, 'label': val_labels})

# --------------------------
# 3️⃣ Tokenization
# --------------------------
tokenizer = BertTokenizer.from_pretrained('nlpaueb/legal-bert-base-uncased')

def tokenize(batch):
    return tokenizer(batch['text'], padding=True, truncation=True, max_length=512)

train_dataset = train_dataset.map(tokenize, batched=True)
val_dataset = val_dataset.map(tokenize, batched=True)

train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])
val_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])

# --------------------------
# 4️⃣ Model Initialization
# --------------------------
num_labels = len(labels)
model = BertForSequenceClassification.from_pretrained('nlpaueb/legal-bert-base-uncased', num_labels=num_labels)

# --------------------------
# 5️⃣ Training Arguments
# --------------------------
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../models/legalbert_clause')

training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    evaluation_strategy="epoch",       # correct for 4.56.2
    save_strategy="epoch",
    logging_dir=os.path.join(output_dir, '../logs'),
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    save_total_limit=1,
)


# --------------------------
# 6️⃣ Metrics Function
# --------------------------
def compute_metrics(eval_pred):
    logits, labels_true = eval_pred
    preds = torch.argmax(torch.tensor(logits), dim=1)
    acc = (preds == torch.tensor(labels_true)).sum().item() / len(labels_true)
    return {'accuracy': acc}

# --------------------------
# 7️⃣ Trainer Setup
# --------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics
)

# --------------------------
# 8️⃣ Train the model
# --------------------------
trainer.train()

# --------------------------
# 9️⃣ Save Model & Tokenizer
# --------------------------
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

print("✅ LegalBERT clause classification model trained and saved successfully.")
