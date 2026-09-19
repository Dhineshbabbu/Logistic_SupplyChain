import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter,RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Load environment variables
project_root = Path(__file__).resolve().parent.parent 
load_dotenv(dotenv_path=project_root / ".env")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is not set in the environment variables.")

#set up clean production data cache path
CACHE_DIR = project_root / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
HASH_FILE = CACHE_DIR / "ingestion_hash_cache.json"

hash_cache = {}
if HASH_FILE.exists():
    with open(HASH_FILE, "r") as f:
        hash_cache = json.load(f)

#Embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

#=============================================
# Connect to Pinecone and create vector store
#=============================================

print("Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)

INDEX_NAME = "sop-embeddings"

existing_indexes = pc.list_indexes().names()

if INDEX_NAME not in existing_indexes:
    print(f"Creating Pinecone index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,  # Dimension of the embedding model
        metric="cosine",
        spec=ServerlessSpec( cloud="aws", region="us-east-1")
        )
else:
    print(f"Pinecone index '{INDEX_NAME}' already exists.")
    pc.delete_index(INDEX_NAME)
    pc.create_index(
            name=INDEX_NAME,
            dimension=384,  # Dimension of the embedding model
            metric="cosine",
            spec=ServerlessSpec( cloud="aws", region="us-east-1")
            )

index_client = pc.Index(INDEX_NAME)
vector_store = PineconeVectorStore(index_client,embedding_model)

#============================================
# Chunking and Ingesting SOP documents
#============================================

doc_path = project_root / "data" / "policy"
src_file_name = ""

for file_name in doc_path.glob("**/*.md"):
    src_file_name = file_name

raw_chunks = []
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=60
    )
extension = src_file_name.suffix.lower()

if extension == ".md":
    header_to_split = [("#", "Header_1"), ("##", "Header_2"), ("###", "Header_3")]
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=header_to_split)
    raw_data = src_file_name.read_text(encoding="utf-8")
    header_docs = md_splitter.split_text(raw_data)
    raw_chunks = text_splitter.split_documents(header_docs)

#Sanity check
final_chunks = []
for chunk in raw_chunks:
    clear_text = chunk.page_content.strip()
    if clear_text:
        chunk.page_content = clear_text
        final_chunks.append(chunk)


ids = []
for idx,chunk in enumerate(final_chunks):
    chunk.metadata["source_file"] = str(src_file_name.name)
    chunk.metadata["document_type"] = "SOP"
    ids.append(f"{src_file_name.name}_chunk_{idx}")


batch_size = 100
total_chunks = len(final_chunks)

for i in range(0,total_chunks,batch_size):
    print(f"inserting chunk {i+1} of {total_chunks}")
    batch_chunks = final_chunks[i:i+batch_size]
    batch_ids = ids[i:i+batch_size]
    vector_store.add_documents(documents=batch_chunks, ids=batch_ids)
