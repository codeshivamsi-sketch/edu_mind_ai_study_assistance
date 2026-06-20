from config import collection, model, anthropic_client
import os

def embed_ques(question: str):
    question_embedding = model.encode(question).tolist()
    return question_embedding

def get_searched_chunks_from_chroma(question_embedding):
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=3
    )
    chunks = results["documents"][0]
    return chunks

def get_ans_from_claud(question, chunks):
    context = "\n\n".join(chunks)
    prompt="You are a helpful assistant. Answer the question using only the context provided. Cite which part of the context you used."
    grouding_context=f"Context:\n{context}\n\nQuestion: {question}"
    response = anthropic_client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=prompt,
        messages=[
            {
                "role": "user", 
                "content": grouding_context
            }
        ]
    )
    return response
    


