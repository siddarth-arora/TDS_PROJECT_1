from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests
from google import genai
from google.genai import types
from pathlib import Path
import numpy as np
from google.genai.types import GenerateContentConfig, HttpOptions

app = FastAPI()

load_dotenv()
genai_api_key = os.getenv("GENAI_API_KEY")
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


def get_image_description(image_path):
    client = genai.Client(api_key=genai_api_key)
    my_file = client.files.upload(file=image_path)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[my_file, "Describe the study-related content in this image, including headings, formulas, and the main topic if identifiable."],
    )

    return response.text


def load_embeddings():
    data = np.load("embeddings.npz", allow_pickle=True)
    return data["chunks"], data['embeddings']


def generate_llm_response(question : str, context : str):
    client = genai.Client(api_key=genai_api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            f"Answer the question based on the context provided.\n\nQuestion: {question}\n\nContext: {context}",
            "You are a helpful assistant that provides concise and accurate answers based on the provided context.",
            "If the context does not contain enough information to answer the question, respond with 'I don't know'.",
            "Your response should be in markdown format, with necessary formatting for code blocks, lists, and headings.",
            "Also provide relvant links to the source material if available from the context"
        ],
        config=GenerateContentConfig(
            max_output_tokens=512,
            temperature=0.2,
            top_p=0.95,
            top_k=40
        )
    )
    return response.text

def answer(question: str, image: str = None):
    loaded_chunks, loaded_embeddings = load_embeddings()
    if image:
        image_description = get_image_description(f"data:image/jpeg;base64,{image}")
        question += f"{image_description}"
    
    question_embedding = get_embedding(question)
    similarities = np.dot(loaded_embeddings, question_embedding) / (
        np.linalg.norm(loaded_embeddings, axis=1) * np.linalg.norm(question_embedding)
    )

    top_indicies = np.argsort(similarities)[-10:][::-1]
    top_chunks = [loaded_chunks[i] for i in top_indicies]

    response = generate_llm_response(question, "\n".join(top_chunks))
    return{
        "question" : question,
        "response" : response,
        "top_chunks" : top_chunks
    }



# class QuestionRequest(BaseModel):
#     question: str
#     image : str = None

@app.post("/api/")
async def api_answer(request : Request):
    try:
        data = await request.json()
        print(data)
        return answer(data.get("question"), data.get("image"))
    except Exception as e:
        return {"error": str(e)}

    




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)