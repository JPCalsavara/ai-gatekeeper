"""
Context Harness indexing and semantic retrieval engine.
Extracts engineering rules, RFCs, and guidelines from the environment,
generates embeddings using Google text-embedding-004, and saves a local JSON index.
Provides cosine similarity retrieval to inject relevant guidelines during PR reviews.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

def normalize_vector(v: List[float]) -> List[float]:
    """Returns the L2-normalized unit vector."""
    norm = sum(x * x for x in v) ** 0.5
    if norm == 0.0:
        return v
    return [x / norm for x in v]

def fast_dot_product(a: List[float], b: List[float]) -> float:
    """Calculates fast dot product between pre-normalized float vectors."""
    return sum(x * y for x, y in zip(a, b))

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculates cosine similarity between two float vectors in pure Python."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

def chunk_markdown(file_path: Path) -> List[Dict[str, str]]:
    """Splits a markdown file into logical chunks by section headings."""
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    chunks = []
    current_title = file_path.name
    current_lines = []

    for line in lines:
        if line.startswith("#"):
            if current_lines:
                chunk_text = "\n".join(current_lines).strip()
                if chunk_text:
                    chunks.append({
                        "source": str(file_path),
                        "title": current_title,
                        "content": chunk_text
                    })
                current_lines = []
            current_title = line.lstrip("#").strip()
        current_lines.append(line)

    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            chunks.append({
                "source": str(file_path),
                "title": current_title,
                "content": chunk_text
            })

    return chunks

def build_harness_index(sources: List[Path], output_file: Path = Path("context_harness.json")) -> int:
    """Scans document sources, computes embeddings, and writes the local JSON vector store."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY or GEMINI_API_KEY for embedding generation.")

    embeddings_model = GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"),
        google_api_key=api_key
    )

    all_chunks = []
    for src in sources:
        if src.is_file():
            all_chunks.extend(chunk_markdown(src))
        elif src.is_dir():
            for p in src.glob("**/*.md"):
                all_chunks.extend(chunk_markdown(p))

    if not all_chunks:
        print("[WARN] No markdown chunks found to index.")
        return 0

    texts = [f"{c['title']}\n{c['content']}" for c in all_chunks]
    vectors = []
    batch_size = 15
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for attempt in range(5):
            try:
                batch_vectors = embeddings_model.embed_documents(batch)
                vectors.extend(batch_vectors)
                break
            except Exception as e:
                if ("RESOURCE_EXHAUSTED" in str(e) or "429" in str(e)) and attempt < 4:
                    import time
                    wait_s = 20 * (attempt + 1)
                    print(f"[WARN] Embedding quota limit hit. Retrying in {wait_s}s (attempt {attempt + 1}/5)...")
                    time.sleep(wait_s)
                else:
                    raise e

    index_data = []
    for idx, (chunk, vector) in enumerate(zip(all_chunks, vectors)):
        norm_vector = normalize_vector(vector)
        index_data.append({
            "id": f"chunk_{idx}",
            "source": chunk["source"],
            "title": chunk["title"],
            "content": chunk["content"],
            "embedding": norm_vector
        })

    output_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
    print(f"[SUCCESS] Indexed {len(index_data)} chunks into {output_file}")
    return len(index_data)

def retrieve_relevant_guidelines(query: str, index_file: Path = Path("context_harness.json"), top_k: int = 3) -> str:
    """
    Retrieves the top_k most semantically relevant guidelines from context_harness.json.
    Falls back to docs/guidelines.md if index file is not present.
    """
    fallback_file = (index_file.parent / "docs" / "guidelines.md") if index_file.parent != Path(".") else Path("docs/guidelines.md")

    if not index_file.exists():
        if fallback_file.exists():
            return fallback_file.read_text(encoding="utf-8")
        return ""

    try:
        data = json.loads(index_file.read_text(encoding="utf-8"))
        if not data:
            return ""

        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Fallback to static text if no API key is available for query embedding
            return fallback_file.read_text(encoding="utf-8") if fallback_file.exists() else ""

        embeddings_model = GoogleGenerativeAIEmbeddings(
            model=os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"),
            google_api_key=api_key
        )
        raw_query_vector = embeddings_model.embed_query(query[:1000])  # Cap query length
        q_norm = normalize_vector(raw_query_vector)

        scored_chunks: List[Tuple[float, Dict]] = []
        if HAVE_NUMPY and len(data) > 10:
            emb_matrix = np.array([item["embedding"] for item in data], dtype=float)
            q_arr = np.array(q_norm, dtype=float)
            sims = np.dot(emb_matrix, q_arr)
            scored_chunks = [(float(s), item) for s, item in zip(sims, data)]
        else:
            for item in data:
                sim = fast_dot_product(q_norm, item.get("embedding", []))
                scored_chunks.append((sim, item))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, item in scored_chunks[:top_k]:
            results.append(f"### {item['title']} (Source: {item['source']}, Relevance: {score:.2f})\n{item['content']}")

        return "\n\n".join(results)
    except Exception as e:
        print(f"[WARN] Error in semantic retrieval: {e}. Using fallback.")
        return fallback_file.read_text(encoding="utf-8") if fallback_file.exists() else ""
