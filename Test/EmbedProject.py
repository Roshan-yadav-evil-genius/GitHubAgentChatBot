from langchain_community.document_loaders import UnstructuredMarkdownLoader,DirectoryLoader,PythonLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


model_embedding = OllamaEmbeddings(model="nomic-embed-text:latest")
vectore_store = Chroma(embedding_function=model_embedding,persist_directory="./vectorstore")


markdown_loader = DirectoryLoader(
    "C:/Users/roshan.yadav/13thWonder/the_special_nine_day/Github/",
    glob="**/*.md",
    loader_cls=UnstructuredMarkdownLoader,
    show_progress=True,
    use_multithreading=True,
)

python_loader = DirectoryLoader(
    "C:/Users/roshan.yadav/13thWonder/the_special_nine_day/Github/",
    glob="**/*.py",
    loader_cls=PythonLoader,
    show_progress=True,
    use_multithreading=True,
)

docs = python_loader.load()
# docs = markdown_loader.load() + python_loader.load()

doc_sources = [doc.metadata["source"] for doc in docs]
print(doc_sources)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

smaller_documents = text_splitter.split_documents(docs)

vectore_store.add_documents(documents=smaller_documents)