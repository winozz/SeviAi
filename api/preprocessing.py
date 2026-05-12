"""
Shared text preprocessing for SeviAi training and inference.
The trainer and runtime classifier MUST use the same function — when they
diverge the model silently mispredicts at inference time.
"""

import re
from functools import lru_cache

import nltk
from nltk.stem import WordNetLemmatizer

# Ensure NLTK resources are available at import time
for _resource in ("punkt_tab", "wordnet"):
    try:
        nltk.data.find(f"tokenizers/{_resource}" if _resource.startswith("punkt") else f"corpora/{_resource}")
    except LookupError:
        nltk.download(_resource, quiet=True)

_lemmatizer = WordNetLemmatizer()

# Deliberately small stoplist. We do NOT use sklearn's `stop_words='english'`
# because it strips wh-words (what/where/when/how) which are the highest-signal
# tokens for short user questions like "Where is CvSU?".
_STOP = frozenset({"the", "a", "an", "of", "to", "in", "is", "it"})

# Keep unicode word characters (so Filipino/Spanish diacritics survive),
# drop punctuation. Replace with space so we don't merge tokens.
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+")


@lru_cache(maxsize=8192)
def _lemmatize_cached(token: str) -> str:
    return _lemmatizer.lemmatize(token)


def preprocess_text(text: str) -> str:
    """Lowercase, strip punctuation, lemmatize ASCII tokens, drop tiny stopwords."""
    if not text:
        return ""
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    if not text:
        return ""
    out = []
    for tok in text.split():
        if tok in _STOP:
            continue
        if tok.isascii() and tok.isalpha():
            tok = _lemmatize_cached(tok)
        out.append(tok)
    return " ".join(out)
