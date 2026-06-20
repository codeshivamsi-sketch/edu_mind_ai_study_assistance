from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

async def save_pdf_on_disk(file):
    contents = await file.read()
    os.makedirs("uploads", exist_ok=True)
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)
    return


def get_pdf_content(filename: str):
    reader = PdfReader(filename)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()
    return full_text

def split_content_into_chunks(filename: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(full_text)
    print(f"Spiltted into: {len(chunks)} chunks")
    return chunks


def embed_chunks(chunks: list[str]):
    embeddings = model.encode(chunks)
    return embeddings.tolist()


def store_in_chroma(chunks: list[str], embeddings: list):
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[str(i) for i in range(len(chunks))]
    )



    
    