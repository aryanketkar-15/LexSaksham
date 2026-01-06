import pandas as pd
import json
import random
from pathlib import Path
from sklearn.model_selection import train_test_split

# CONFIGURATION
INPUT_CSV = "backend/ai_service/models/prepared_data.csv"
OUTPUT_TRAIN = "backend/ai_service/datasets/train_balanced.jsonl"
OUTPUT_TEST = "backend/ai_service/datasets/test_balanced.jsonl"
OUTPUT_MAP = "backend/ai_service/datasets/label_map.json"

# CHANGE THIS to the string name of your majority class found in the logs
MAJORITY_CLASS_NAME = "Obligations" 
KEEP_RATIO = 0.3  # Keep only 30% of this class

def balance_and_convert():
    path = Path(INPUT_CSV)
    if not path.exists():
        print(f"Error: Could not find {path}")
        return

    print(f"Reading {path}...")
    df = pd.read_csv(path)
    
    # 1. Rename columns if needed
    if 'clause_text' in df.columns:
        df = df.rename(columns={'clause_text': 'text'})
    if 'clause_type' in df.columns:
        df = df.rename(columns={'clause_type': 'label'})

    # 2. Generate Label Mapping (String -> Int)
    unique_labels = sorted(df['label'].unique())
    label_map = {label: idx for idx, label in enumerate(unique_labels)}
    
    print(f"Generated Mapping for {len(unique_labels)} classes.")
    # Save mapping so you know what ID 13 represents later
    with open(OUTPUT_MAP, 'w') as f:
        json.dump(label_map, f, indent=2)
    print(f"Saved label map to {OUTPUT_MAP}")

    # 3. Downsample
    print(f"Original Count for '{MAJORITY_CLASS_NAME}': {len(df[df['label'] == MAJORITY_CLASS_NAME])}")
    
    df_majority = df[df['label'] == MAJORITY_CLASS_NAME]
    df_others = df[df['label'] != MAJORITY_CLASS_NAME]

    if len(df_majority) > 0:
        df_majority_downsampled = df_majority.sample(frac=KEEP_RATIO, random_state=42)
        print(f"Downsampled '{MAJORITY_CLASS_NAME}' to {len(df_majority_downsampled)} rows.")
        df_balanced = pd.concat([df_others, df_majority_downsampled])
    else:
        print(f"WARNING: Class '{MAJORITY_CLASS_NAME}' not found! Check spelling.")
        df_balanced = df_others

    # Shuffle
    df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)

    # 4. Map strings to Integers
    df_balanced['label_id'] = df_balanced['label'].map(label_map)

    # 5. Split Train/Test
    # We create a FRESH test set here to ensure IDs match the new training set
    train_df, test_df = train_test_split(df_balanced, test_size=0.1, random_state=42, stratify=df_balanced['label_id'])

    def save_jsonl(dataframe, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            for _, row in dataframe.iterrows():
                # Save 'label' as the INTEGER ID
                f.write(json.dumps({"text": row['text'], "label": int(row['label_id'])}) + "\n")

    print(f"Saving new balanced TRAIN file to {OUTPUT_TRAIN}...")
    save_jsonl(train_df, OUTPUT_TRAIN)

    print(f"Saving new matching TEST file to {OUTPUT_TEST}...")
    save_jsonl(test_df, OUTPUT_TEST)

    print("Done! Use these NEW files for training and evaluation.")

if __name__ == "__main__":
    balance_and_convert()