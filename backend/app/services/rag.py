import os
import json
import math
import unicodedata
from typing import List, Dict, Any, Tuple
from collections import Counter
from app.config import settings

KB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "knowledge_base", "raw", "medical_kb_bn.json"
)

BANGLA_STOPWORDS = {
    "কি", "কী", "কে", "কেন", "কার", "কিভাবে", "হলে", "হলো", "হলে কি", "বা", "ও", "এবং", "আর",
    "হয়", "হবে", "হচ্ছে", "করে", "করলে", "করব", "করবেন", "করা", "জন্য", "থেকে", "দিয়ে", "দিতে",
    "আছে", "নেই", "একটি", "এই", "সেই", "তা", "এর", "দেয়", "গেলে", "না", "যদি", "মতো", "খুব"
}

def normalize_bangla_text(text: str) -> str:
    """
    Normalizes Bengali Unicode representations:
    - Normalizes decomposed ya (\u09af\u09bc -> \u09df)
    - Normalizes decomposed da/rha (\u09a1\u09bc -> \u09dc, \u09a2\u09bc -> \u09dd)
    - Standardizes NFC/NFKC forms
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u09af\u09bc", "\u09df")  # য + ় -> য়
    text = text.replace("\u09a1\u09bc", "\u09dc")  # ড + ় -> ড়
    text = text.replace("\u09a2\u09bc", "\u09dd")  # ঢ + ় -> ঢ়
    text = text.replace("িয়া", "িয়া")
    return text

class BanglaRAGService:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.doc_freq: Counter = Counter()
        self.num_docs: int = 0
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        if os.path.exists(KB_PATH):
            try:
                with open(KB_PATH, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                    self.num_docs = len(self.chunks)
                    for chunk in self.chunks:
                        tokens = set(self._tokenize(chunk["title"] + " " + chunk["text"]))
                        for t in tokens:
                            self.doc_freq[t] += 1
            except Exception as e:
                print(f"Error loading knowledge base: {e}")
                self.chunks = []

    def _tokenize(self, text: str) -> List[str]:
        text = normalize_bangla_text(text.lower())
        for p in "।,?!:;\"'()[]{}<>-/\\":
            text = text.replace(p, " ")
        tokens = [w.strip() for w in text.split() if len(w.strip()) > 1]
        return [t for t in tokens if t not in BANGLA_STOPWORDS]

    def retrieve(self, query: str, top_k: int = 3) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Retrieves top_k relevant medical chunks based on TF-IDF relevance with Unicode normalization.
        """
        if not self.chunks or not query:
            return [], False

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return [], False

        scored_chunks = []
        for chunk in self.chunks:
            title_tokens = set(self._tokenize(chunk["title"]))
            body_tokens = self._tokenize(chunk["text"])
            chunk_tokens = title_tokens.union(set(body_tokens))

            score = 0.0
            for qt in query_tokens:
                if qt in chunk_tokens:
                    df = self.doc_freq.get(qt, 1)
                    idf = math.log((self.num_docs + 1) / (df + 0.5)) + 1.0
                    weight = 3.0 if qt in title_tokens else 1.0
                    score += idf * weight

            if score > 0:
                normalized_score = min(1.0, score / (len(query_tokens) * 3.5 + 1e-5))
                scored_chunks.append({
                    "id": chunk["id"],
                    "title": chunk["title"],
                    "source": chunk["source"],
                    "text": chunk["text"],
                    "score": round(normalized_score, 3)
                })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_chunks[:top_k]

        top_score = top_results[0]["score"] if top_results else 0.0
        is_confident = top_score >= settings.KB_CONFIDENCE_THRESHOLD

        return top_results, is_confident

rag_service = BanglaRAGService()
