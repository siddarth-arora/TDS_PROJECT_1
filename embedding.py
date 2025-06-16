'''
from semantic_text_splitter import MarkdownSplitter
from tqdm import tqdm
from pathlib import Path
import requests
import os
from dotenv import load_dotenv
import time
import numpy as np


# # Get chunks from a markdown file
# def get_chunks(file_path, chunk_size=1000):
#     with open(file_path, 'r', encoding='utf-8') as file:
#         content = file.read()
    
#     splitter = MarkdownSplitter(chunk_size)
#     chunks = splitter.chunks(content)
    
#     return chunks


# Get overlapping chunks from a markdown file
def get_chunks(file_path, chunk_size=1000, overlap=200):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Use a slightly larger chunk size to allow overlap
    splitter = MarkdownSplitter(chunk_size + overlap)
    initial_chunks = splitter.chunks(content)

    # Add overlap by sliding window over each chunk
    final_chunks = []
    for chunk in initial_chunks:
        start = 0
        while start < len(chunk):
            end = start + chunk_size
            sub_chunk = chunk[start:end]
            if sub_chunk.strip():  # skip empty chunks
                final_chunks.append(sub_chunk)
            if end >= len(chunk):
                break
            start += chunk_size - overlap  # slide window with overlap

    return final_chunks



load_dotenv()
aiproxy_apikey = os.getenv("AIPROXY_TOKEN")


# Get embeddings for a list of texts
def get_embedding(text: str) -> list:
    url = "https://aiproxy.sanand.workers.dev/openai/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {aiproxy_apikey}"
    }
    data = {
        "model": "text-embedding-3-small",
        "input": text
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]
    except Exception as e:
        print(f"Error fetching embedding: {e}")
        return []


files = [*Path("markdown").glob("*.md"), *Path("markdown").rglob("*.md")]
all_chunks = []
all_embeddings = []
total_chunks = 0
file_chunks = {}
for file_path in files:
    chunks = get_chunks(file_path)
    file_chunks[file_path] = chunks
    total_chunks += len(chunks)

print(f"Total chunks to process: {total_chunks}")

with tqdm(total=total_chunks, desc="Processing embeddings") as pbar:
    for file_path, chunks in file_chunks.items():
        for chunk in chunks:
            try:
                embedding = get_embedding(chunk)
                all_chunks.append(chunk)
                all_embeddings.append(embedding)
                pbar.set_postfix({"file": file_path.name, "chunks": len(all_chunks)})
            except Exception as e:
                print(f"Error processing chunk from {file_path}: {e}")
                continue
            finally:
                pbar.update(1)

np.savez(
    "embeddings.npz",
    chunks=all_chunks,
    embeddings=all_embeddings
)'''



from semantic_text_splitter import MarkdownSplitter
from tqdm import tqdm
from pathlib import Path
import requests
import os
from dotenv import load_dotenv
import time
import numpy as np

# Overlapping chunk extraction from markdown file
def get_chunks(file_path, chunk_size=1000, overlap=200):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    splitter = MarkdownSplitter(chunk_size + overlap)
    initial_chunks = splitter.chunks(content)

    final_chunks = []
    for chunk in initial_chunks:
        start = 0
        while start < len(chunk):
            end = start + chunk_size
            sub_chunk = chunk[start:end]
            if sub_chunk.strip():
                final_chunks.append({
                    "text": sub_chunk,
                    "file": file_path.name
                })
            if end >= len(chunk):
                break
            start += chunk_size - overlap

    return final_chunks

# Load environment variables
load_dotenv()
aiproxy_apikey = os.getenv("AIPROXY_TOKEN")

# Get embedding for a given text
def get_embedding(text: str) -> list:
    url = "https://aiproxy.sanand.workers.dev/openai/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {aiproxy_apikey}"
    }
    data = {
        "model": "text-embedding-3-small",
        "input": text
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]
    except Exception as e:
        print(f"Error fetching embedding: {e}")
        return []

# Retry-safe wrapper
def get_embedding_safe(text, retries=3, delay=2):
    for i in range(retries):
        embedding = get_embedding(text)
        if embedding:
            return embedding
        print(f"⚠️ Retry {i+1} failed. Retrying after {delay}s...")
        time.sleep(delay)
    print("❌ Failed after retries.")
    return []

# Load markdown files
files = [*Path("markdown").glob("*.md"), *Path("markdown").rglob("*.md")]
file_chunks = {}
total_chunks = 0

for file_path in files:
    chunks = get_chunks(file_path)
    file_chunks[file_path] = chunks
    total_chunks += len(chunks)

print(f"Total chunks to process: {total_chunks}")

# Checkpoint support
checkpoint_path = "checkpoint_embeddings.npz"
all_chunks, all_embeddings, seen_hashes = [], [], set()

if Path(checkpoint_path).exists():
    checkpoint = np.load(checkpoint_path, allow_pickle=True)
    all_chunks = list(checkpoint["chunks"])
    all_embeddings = list(checkpoint["embeddings"])
    seen_hashes = set(hash(c["text"]) for c in all_chunks)
    print(f"✅ Resumed from checkpoint: {len(all_chunks)} chunks loaded.")

# Main loop with tqdm
with tqdm(total=total_chunks, desc="Processing embeddings", initial=len(all_chunks)) as pbar:
    for file_path, chunks in file_chunks.items():
        for chunk in chunks:
            chunk_text = chunk["text"]
            if hash(chunk_text) in seen_hashes:
                continue  # Skip already processed

            embedding = get_embedding_safe(chunk_text)
            if not embedding:
                continue

            all_chunks.append(chunk)
            all_embeddings.append(embedding)
            seen_hashes.add(hash(chunk_text))
            pbar.set_postfix({"file": file_path.name, "chunks": len(all_chunks)})
            pbar.update(1)

            # Save checkpoint every 50 chunks
            if len(all_chunks) % 50 == 0:
                np.savez(checkpoint_path, chunks=all_chunks, embeddings=all_embeddings)
                print(f"💾 Checkpoint saved at {len(all_chunks)} chunks.")

# Final save
print(len(all_chunks))
print(len(seen_hashes))
np.savez("embeddings.npz", chunks=all_chunks, embeddings=all_embeddings)
print("✅ All embeddings saved successfully.")

