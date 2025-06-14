from semantic_text_splitter import MarkdownSplitter
from tqdm import tqdm
from pathlib import Path
import requests
import os
from dotenv import load_dotenv
import time
import numpy as np


# Get chunks from a markdown file
def get_chunks(file_path, chunk_size=1000):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    splitter = MarkdownSplitter(chunk_size)
    chunks = splitter.chunks(content)
    
    return chunks


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
)
