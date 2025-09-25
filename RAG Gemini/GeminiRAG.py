import streamlit as st
import faiss
import os
import tempfile
import numpy as np
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
import docx

# Configure Google Gemini API
genai.configure(api_key="AIzaSyBxxiPTIRH1M2SUEbzFCyUT5TU1BGtZphs")
MODEL_NAME = "gemini-1.5-flash"  # Update model name as required
SYSTEM_PROMPT = """
You are a financial and business analyst. As a CEO, I do not have time to read all the documents.
Your task is to summarize the document and share the summary of the results:
1) Bullet points
2) Proper headings
3) Visualizations like charts and graphs for better reading
Only perform additional tasks on the document as explicitly mentioned by me.
"""

# Initialize embedding model and FAISS index
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Embedding model
FAISS_INDEX_FILE = "index.faiss"

# Load or create FAISS index
if os.path.exists(FAISS_INDEX_FILE):
    faiss_index = faiss.read_index(FAISS_INDEX_FILE)
else:
    faiss_index = faiss.IndexFlatL2(384)  # Use dimension based on embedding model

# Global variable to hold documents
document_list = []

# Utility functions
def embed_text(text):
    """Generate embedding for a given text."""
    return embedding_model.encode([text])[0]

def create_faiss_index(docs):
    """Create or update FAISS index with uploaded documents."""
    embeddings = [embed_text(doc) for doc in docs]
    vectors = np.array(embeddings).astype("float32")
    faiss_index.add(vectors)
    
    # Keep track of the original documents
    document_list.extend(docs)  # Store documents in a list

def save_faiss_index():
    """Save FAISS index to disk."""
    faiss.write_index(faiss_index, FAISS_INDEX_FILE)

def retrieve_documents(query, top_k=3):
    """Retrieve top-k relevant document sections based on similarity to the query."""
    query_embedding = embed_text(query).astype("float32")
    D, I = faiss_index.search(np.array([query_embedding]), top_k)
    return I[0]  # Return indices of top-k documents

def query_gemini_system(prompt, documents):
    """Query the Gemini model for a response based on the retrieved documents."""
    # Combine documents with system prompt and user query
    prompt_with_docs = SYSTEM_PROMPT + "\n\n" + "\n\n".join(documents) + f"\n\nUser query: {prompt}"
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt_with_docs)
    return response.text.strip()

def read_document(file_path, file_type):
    """Read the content of different types of documents."""
    content = ""
    if file_type == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
    elif file_type == "pdf":
        with open(file_path, "rb") as file:
            pdf = PdfReader(file)
            for page in pdf.pages:
                content += page.extract_text() or ""  # Handle None if no text found
    elif file_type == "docx":
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            content += para.text
    return content

# Streamlit UI
st.title("RAG-based Document Query System with Google Gemini")

# Step 1: Document Upload
uploaded_file = st.file_uploader("Upload a document to add to the knowledge base", type=["txt", "pdf", "docx"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        tmp_file_path = tmp_file.name
    
    # Detect the file type
    file_type = uploaded_file.type.split('/')[1]
    
    # Read and index document content based on file type
    content = read_document(tmp_file_path, file_type)
    st.success(f"{file_type.upper()} document uploaded successfully.")
    
    # Add document to FAISS index
    create_faiss_index([content])
    save_faiss_index()
    st.write("Document indexed successfully.")

# Step 2: Query the RAG System
st.write("## Query the Knowledge Base")
user_query = st.text_input("Enter your query here:")

if st.button("Get Answer"):
    if user_query:
        # Retrieve relevant documents
        indices = retrieve_documents(user_query)
        
        # Check if any indices were retrieved
        if indices.size == 0:
            st.warning("No relevant documents found for your query.")
        else:
            relevant_docs = [document_list[i] for i in indices if i < len(document_list)]  # Get original documents
            
            # Generate response using Google Gemini
            if relevant_docs:  # Check if relevant_docs is not empty
                answer = query_gemini_system(user_query, relevant_docs)
                st.write("### Answer:")
                st.write(answer)
            else:
                st.warning("No relevant documents found for the retrieved indices.")
    else:
        st.warning("Please enter a query.")
