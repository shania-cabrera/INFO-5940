import streamlit as st
from openai import AzureOpenAI
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb
from os import environ


st.title("Assignment 1: RAG Application")
st.caption("Designed by Shania Cabrera")

client = AzureOpenAI(
    api_key=environ['AZURE_OPENAI_API_KEY'],
    api_version="2023-03-15-preview",
    azure_endpoint=environ['AZURE_OPENAI_ENDPOINT'],
    azure_deployment=environ['AZURE_OPENAI_MODEL_DEPLOYMENT'],
)

embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-large")

uploaded_files = st.file_uploader("Please upload file(s)", type=("txt", "pdf"), accept_multiple_files=True)

chunk_size = 100
chunk_overlap = 0
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap
)s

if uploaded_files:
    documents = []
    for uploaded_file in uploaded_files:
        file_path = path.join("/tmp", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        if uploaded_file.type == "text/plain":
            loader = TextLoader(file_path)
        elif uploaded_file.type == "application/pdf":
            loader = PyPDFLoader(file_path)
        else:
            st.error(f"Unsupported file type: {uploaded_file.type}")
            remove(file_path)
            continue
        
        documents.extend(loader.load())
        remove(file_path)

    chunks = text_splitter.split_documents(documents)

    client = chromadb.Client()
    collection_name = "langchain"
    client.delete_collection(collection_name)
    
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings)
    st.success("Documents processed and indexed successfully!")


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you with the uploaded documents?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


if 'vectorstore' in locals():
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})
    template = """
    You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    
    Question: {question} 
    
    Context: {context} 
    
    Answer:
    """
    prompt = PromptTemplate.from_template(template)


    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    question = st.chat_input("Ask about the documents", disabled=not uploaded_files)

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        with st.chat_message("assistant"):
            response = rag_chain.invoke(question)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.info("Please upload documents to start the conversation.")

if st.checkbox("Show document chunks"):
    if 'chunks' in locals():
        for i, chunk in enumerate(chunks):
            st.write(f"Chunk {i+1}:")
            st.write(chunk.page_content)
            st.write("-----")
    else:
        st.info("No documents have been processed yet.")