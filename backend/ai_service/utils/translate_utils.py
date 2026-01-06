"""
Translation Utilities using MarianMT (Helsinki-NLP)
--------------------------------------------------
Provides simple helpers for translate-first multilingual processing:
- translate_to_en(text, src_hint=None): Hindi/Marathi → English
- translate_to_hi(text): English → Hindi (back-translation)

Notes:
- Models are loaded lazily and cached.
- Uses GPU if available, otherwise CPU.
- Marathi back-translation can be added similarly if needed.
"""

from typing import Optional
from functools import lru_cache
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def _get_hi_en():
    try:
        tok = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-hi-en")
        mdl = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-hi-en").to(DEVICE)
        return tok, mdl
    except Exception as e:
        print("⚠️ Failed to load Helsinki-NLP/opus-mt-hi-en tokenizer/model:", e)
        print("   Hint: install 'sentencepiece' (pip install sentencepiece) to enable MarianMT tokenizers.")
        return None, None


@lru_cache(maxsize=1)
def _get_mr_en():
    try:
        tok = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-mr-en")
        mdl = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-mr-en").to(DEVICE)
        return tok, mdl
    except Exception as e:
        print("⚠️ Failed to load Helsinki-NLP/opus-mt-mr-en tokenizer/model:", e)
        print("   Hint: install 'sentencepiece' (pip install sentencepiece) to enable MarianMT tokenizers.")
        return None, None


@lru_cache(maxsize=1)
def _get_en_hi():
    try:
        tok = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-hi")
        mdl = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-hi").to(DEVICE)
        return tok, mdl
    except Exception as e:
        print("⚠️ Failed to load Helsinki-NLP/opus-mt-en-hi tokenizer/model:", e)
        print("   Hint: install 'sentencepiece' (pip install sentencepiece) to enable MarianMT tokenizers.")
        return None, None


def _generate(model, tokenizer, text: str, max_length: int = 256) -> str:
    # If tokenizer/model failed to load, return original text as a safe fallback
    if tokenizer is None or model is None:
        print("⚠️ Translation model/tokenizer unavailable — returning original text.")
        return text

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=256)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    with torch.no_grad():
        ids = model.generate(**inputs, max_length=max_length, num_beams=4)
    return tokenizer.decode(ids[0], skip_special_tokens=True)


def translate_to_en(text: str, src_hint: Optional[str] = None) -> str:
    """Translate Hindi/Marathi text to English.

    If src_hint is provided and one of {"hi", "mr"}, use the corresponding model.
    Otherwise defaults to Hindi→English.
    """
    src = (src_hint or "hi").lower()
    if src == "mr":
        tok, mdl = _get_mr_en()
    else:
        tok, mdl = _get_hi_en()

    # If model/tokenizer is not available, return original text (no translation)
    if tok is None or mdl is None:
        return text

    try:
        return _generate(mdl, tok, text)
    except Exception:
        # Fallback to Hindi→English if Marathi fails
        tok_f, mdl_f = _get_hi_en()
        if tok_f is None or mdl_f is None:
            return text
        return _generate(mdl_f, tok_f, text)


def translate_to_hi(text: str) -> str:
    """Translate English text to Hindi (back-translation)."""
    tok, mdl = _get_en_hi()
    if tok is None or mdl is None:
        return text
    return _generate(mdl, tok, text)