import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

stop_words = stopwords.words('english')

def preprocess_text(text):
    """
    Basic preprocessing: lowercase, remove non-alpha words, remove stopwords
    """
    text = text.lower()
    cleaned = ' '.join(word for word in text.split() if word.isalpha() and word not in stop_words)
    return cleaned

def risk_score(text):
    """
    Rule-based risk scoring
    """
    high_risk_keywords = ['terminate', 'penalty', 'liability', 'indemnify']
    score = sum(word in text.lower() for word in high_risk_keywords)
    if score >= 2:
        return 'High'
    elif score == 1:
        return 'Medium'
    else:
        return 'Low'
