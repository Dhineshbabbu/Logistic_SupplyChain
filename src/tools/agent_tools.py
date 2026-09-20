import os
import streamlit as st
import re
import requests
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

#=====================================================================
# 1. Load environment variables, Embeddings and Pinecone Vector Store
#=====================================================================

project_root = Path(__file__).resolve().parent.parent.parent
print(f"Project Root: {project_root}")
load_dotenv(dotenv_path=project_root / ".env")

PINECONE_API_KEY = st.secrets.get(
    "PINECONE_API_KEY",
    os.getenv("PINECONE_API_KEY")
)

db_host = st.secrets.get("DB_HOST", os.getenv("DB_HOST"))
db_port = st.secrets.get("DB_PORT", os.getenv("DB_PORT"))
db_name = st.secrets.get("DB_NAME", os.getenv("DB_NAME"))
db_user = st.secrets.get("DB_USER", os.getenv("DB_USER"))
db_password = st.secrets.get("DB_PASSWORD", os.getenv("DB_PASSWORD"))

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is not set in the environment variables.")

if not db_host or not db_port or not db_name or not db_user or not db_password:
    raise ValueError("Database connection variables are not set in the environment variables.")

INDEX_NAME = "sop-embeddings"
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
pinecone_vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embedding_model)

## RETRIEVE
retriever = pinecone_vector_store.as_retriever(search_kwargs={"k": 2})

#===========================
# 2. Core FDE Agent Tools
#===========================

@tool(description="Retrieve relevant information from the Postgres database based on the query.")
def retrieve_from_postgres(sql_query: str) -> str:
    # create a connecting string
    connection_string = (
    f"postgresql://{quote_plus(db_user)}:"
    f"{quote_plus(db_password)}@"
    f"{db_host}:{db_port}/{db_name}"
)

    engine = create_engine(connection_string)

    query = sql_query.strip().rstrip(";")

    if not re.match(r"(?is)^SELECT\b", query):
        return "ERROR: Only SELECT queries are allowed."

    # Reject common dangerous SQL keywords
    forbidden = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "GRANT",
        "REVOKE"
    ]

    for keyword in forbidden:
        if re.search(rf"\b{keyword}\b", query, re.IGNORECASE):
            return f"ERROR: SQL keyword {keyword} is not allowed."

    # --------------------------------
    # 3. Validate table name
    # --------------------------------

    if re.search(r"\bshipments\b", query, re.IGNORECASE):
        return (
            "ERROR: Table 'shipments' does not exist. "
            "Use the correct table: logistics_data."
        )

    if not re.search(r"\blogistics_data\b", query, re.IGNORECASE):
        return (
            "ERROR: Query must use the logistics_data table."
        )

    # --------------------------------
    # 4. Execute SQL
    # --------------------------------

    try:

        with engine.connect() as connection:
            result = connection.execute(text(query))
            rows = result.fetchall()
            columns = list(result.keys())
            result_str = "\n".join(
                [
                    str(dict(zip(columns, row)))
                    for row in rows
                ]
            )

            if not result_str:
                return "No matching records found."

            return result_str

    except Exception as e:

        return (
            f"ERROR: SQL execution failed.\n"
            f"Details: {str(e)}"
        )

    finally:
        engine.dispose()

@tool(description="Retrieve relevant information from the Pinecone vector store based on the query.")
def retrieve_from_pinecone(query: str) -> str:
    docs = retriever.invoke(query)
    # Convert the documents to a string representation
    result_str = "\n".join([doc.page_content for doc in docs])
    return result_str

@tool(description="Retrieve the current Weather Conditions")
def fetch_weather_conditions(latitude: float, longitude: float) -> str:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
        response = requests.get(url, timeout=6)
        response.raise_for_status()
        
        payload = response.json().get("current_weather", {})
        temp = payload.get("temperature", "N/A")
        wind = payload.get("windspeed", 0.0)
        
        return (
            f"--- LIVE CORRIDOR TELEMETRY ---\n"
            f"Target GPS: {latitude}, {longitude}\n"
            f"External Temp: {temp}°C | Wind Speed: {wind} km/h\n"
            f"-------------------------------"
        )


# ==========================================
# 3. LOCAL VERIFICATION
# ==========================================
if __name__ == "__main__":
    print("\n--- Testing Tool 1: SQL Telemetry View ---")
    print(retrieve_from_postgres.invoke("SELECT * FROM logistics_data;"))
    
    print("\n--- Testing Tool 2: Live Corridor API ---")
    print(fetch_weather_conditions.invoke({"latitude": 33.77, "longitude": -118.19}))
    
    print("\n--- Testing Tool 3: Pinecone Vector Retrieval ---")
    print(retrieve_from_pinecone.invoke("What are the temperature rules for fresh perishables?"))