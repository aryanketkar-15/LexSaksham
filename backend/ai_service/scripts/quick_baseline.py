# backend/ai_service/scripts/quick_baseline.py
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "clause_dataset" / "prepared"
train = DATA_DIR / "train.jsonl"
test  = DATA_DIR / "test.jsonl"

def read_jsonl(path):
    X,Y=[],[]
    with open(path,"r",encoding="utf8") as f:
        for line in f:
            j=json.loads(line)
            X.append(j.get("text",""))
            Y.append(j.get("label"))
    return X,Y

if not train.exists() or not test.exists():
    print("train.jsonl/test.jsonl not found in prepared/. Use your own file names")
    raise SystemExit(1)

Xtr, Ytr = read_jsonl(train)
Xte, Yte = read_jsonl(test)

vec = TfidfVectorizer(ngram_range=(1,2), max_features=30000)
Xtr_v = vec.fit_transform(Xtr)
Xte_v = vec.transform(Xte)

clf = LogisticRegression(max_iter=2000, solver="saga", C=1.0)
clf.fit(Xtr_v, Ytr)
pred = clf.predict(Xte_v)
print("Acc:", accuracy_score(Yte, pred))
print(classification_report(Yte, pred, zero_division=0))
