import argparse
import os
import fitz
import numpy as np
from app.core.embeddings import get_model
from app.core.vectorstore import get_vectorstore

def chunk_text(text, chunk_size=1000, overlap=200):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks

def ingest_single(pdf_path, doc_id, embedder, vs):
    doc = fitz.open(pdf_path)
    all_chunks = []
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        page_chunks = chunk_text(text)
        for idx, chunk in enumerate(page_chunks):
            all_chunks.append({
                "content": chunk,
                "metadata": {"source": doc_id, "page": page_num+1, "chunk": idx+1}
            })
    contents = [c["content"] for c in all_chunks]
    metadatas = [c["metadata"] for c in all_chunks]
    if not contents:
        print(f"No text extracted from {pdf_path}; skipping.")
        return 0
    embeddings = embedder.encode(contents, show_progress_bar=True)
    # Convert each embedding to a plain Python list
    embeddings_list = [emb.tolist() for emb in embeddings]
    vs.add_chunks(contents, embeddings_list, metadatas)
    print(f"Inserted {len(contents)} chunks for {doc_id}")
    return len(contents)

def ingest(path, doc_id=None):
    embedder = get_model()
    vs = get_vectorstore()
    total = 0
    if os.path.isdir(path):
        for name in sorted(os.listdir(path)):
            if not name.lower().endswith('.pdf'):
                continue
            pdf_path = os.path.join(path, name)
            file_doc_id = os.path.splitext(name)[0]
            total += ingest_single(pdf_path, file_doc_id, embedder, vs)
        print(f"Inserted total {total} chunks across PDFs in {path}")
    else:
        file_doc_id = doc_id or os.path.splitext(os.path.basename(path))[0]
        total += ingest_single(path, file_doc_id, embedder, vs)
    return total

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Path to a PDF file or a directory of PDFs")
    parser.add_argument("--doc-id", required=False, help="ID for this document (defaults to filename if omitted)")
    args = parser.parse_args()
    ingest(args.pdf_path, args.doc_id)
