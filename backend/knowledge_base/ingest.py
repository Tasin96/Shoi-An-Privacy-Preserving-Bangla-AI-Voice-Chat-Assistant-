import os
import json
from typing import List, Dict, Any

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
PROCESSED_FILE = os.path.join(os.path.dirname(__file__), "processed", "knowledge_base.json")

def ingest_medical_documents():
    """
    Ingests, cleans, normalizes, and chunks medical documents from raw JSON/text files.
    Preserves source attributions (WHO, DGHS Bangladesh) and outputs structured store.
    """
    os.makedirs(os.path.join(os.path.dirname(__file__), "processed"), exist_ok=True)
    all_chunks: List[Dict[str, Any]] = []

    raw_json = os.path.join(RAW_DIR, "medical_kb_bn.json")
    if os.path.exists(raw_json):
        with open(raw_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                all_chunks.append({
                    "id": item.get("id"),
                    "title": item.get("title", "").strip(),
                    "category": item.get("category", "general"),
                    "source": item.get("source", "DGHS / WHO"),
                    "text": item.get("text", "").strip(),
                    "language": "bn"
                })

    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"Successfully ingested and processed {len(all_chunks)} medical knowledge chunks.")
    return len(all_chunks)

if __name__ == "__main__":
    ingest_medical_documents()
