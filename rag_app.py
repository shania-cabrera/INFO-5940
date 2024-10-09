from openai import AzureOpenAI
import streamlit as st
from os import environ
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

st.title("Assignment 1: RAG Application")
st.caption("Designed by Shania Cabrera")
uploaded_file = st.file_uploader("Please upload a file", type=("txt", "pdf"))

client = AzureOpenAI(
    api_key=environ['AZURE_OPENAI_API_KEY'],
    api_version="2023-03-15-preview",
    azure_endpoint=environ['AZURE_OPENAI_ENDPOINT'],
    azure_deployment=environ['AZURE_OPENAI_MODEL_DEPLOYMENT'],
)

question = st.chat_input(
    "Ask about this file! :) ",
    disabled=not uploaded_file,
)

chunk_size = 100
chunk_overlap = 0
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = chunk_size,
    chunk_overlap = chunk_overlap
)

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Please ask about the file's content."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if question and uploaded_file:
    file_content = uploaded_file.read().decode("utf-8")
    # fix this to also handle pdf files
    print(file_content)

    st.session_state.messages.append({"role": "user", "content": question})
    st.chat_message("user").write(question)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Here's the content of the file:\n\n{file_content}"},
                *st.session_state.messages
            ],
            stream=True
        )
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})
    

loader = TextLoader(uploaded_file)
documents = loader.load()
chunks = text_splitter.split_documents(loader)

for chunk in chunks:
    print(chunk.page_content)
    print("-----")

# loader = PyPDFLoader(file_content)
# documents = loader.load()
