from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader,
    DirectoryLoader,
    PythonLoader,
    NotebookLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from langchain_community.document_loaders.merge import MergedDataLoader
import logging_setup as _
import logging
from langchain_chroma import Chroma
from chromadb import PersistentClient
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_core.tools import StructuredTool
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from typing import Dict
from utils.enumerators import ToolType
from rich import print
import hashlib
from utils.loaded_project import LoadedProject

class DocEmbedder:

    def __init__(self,persistent_client:PersistentClient,embedding_function:Embeddings):
        self.persistent_client = persistent_client
        self.logger = logging.getLogger(__name__)
        self.embedding_function = embedding_function
        self.projec_agent_tool_collection:Chroma = Chroma(
                client=self.persistent_client,
                collection_name="agent_tools",
                embedding_function=self.embedding_function,
            )
    
    def get_project_loader(self,project_path:Path)->MergedDataLoader:
        markdown_loader = DirectoryLoader(
            path=project_path,
            glob="**/*.md",
            loader_cls=UnstructuredMarkdownLoader,
            # show_progress=True,
        )
        python_loader = DirectoryLoader(
            path=project_path,
            glob="**/*.py",
            loader_cls=PythonLoader,
            # show_progress=True,
        )
        notebook_loader = DirectoryLoader(
            path=project_path,
            glob="**/*.ipynb",
            loader_cls=NotebookLoader,
            # show_progress=True,
        )
        
        loader =MergedDataLoader(loaders=[markdown_loader,python_loader,notebook_loader])
        
        return loader

    def generate_embeddings_if_absent(self,loaded_project:LoadedProject):
        
        collection = Chroma(
            client=self.persistent_client,
            collection_name=loaded_project.name,
            embedding_function=self.embedding_function,
            )

        if collection._collection.count() > 0:
            self.logger.debug(f"Embedding for project {loaded_project.name} already exists. Skipping...")
            return collection._collection_name
        
        self.logger.debug(f"Embedding '{loaded_project.name}' project")
        
        loader = self.get_project_loader(loaded_project.path)
        docs = loader.load()
        self.logger.debug(f"Loaded {len(docs)} documents from `{loaded_project.path}`")
    
        # Split into smaller documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        smaller_documents = text_splitter.split_documents(docs)
        self.logger.debug(f"Split into {len(smaller_documents)} smaller documents Embedding...") 
        
        collection.add_documents(documents=smaller_documents)
        self.logger.debug(f"Finished embedding {len(smaller_documents)} documents")
        
        
    def embedd_project_from_dir(self, project_dir:Path):
        if not Path(project_dir).exists():
            raise FileNotFoundError(f"Directory {project_dir} does not exist.")
        
        return self.generate_embeddings_if_absent(Path(project_dir))
    
    @staticmethod
    def generate_id(content: str) -> str:
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def doc_id_exists(collection:Chroma, doc_id: str) -> bool:
        doc = collection.get(ids=[doc_id])
        if doc["ids"]:
            return True
        return False
        
    def embed_tool_if_missing(self,project_agent_tool:StructuredTool,tool_type:ToolType=ToolType.Project):
        # TODO: logic to embedd project agent tool name in metadata and description in the collection
        
        tool_id = self.generate_id(project_agent_tool.name)
        
        if self.doc_id_exists(self.projec_agent_tool_collection,tool_id):
            self.logger.info(f"Tool/Agent {project_agent_tool.name} already exists in the collection. Skipping...")
            return
        
        
        about_tool = PromptTemplate.from_template("""
        tool/agent Name: {name}
        tool/agent Description: {description}
        """)
        
        document = Document(page_content=about_tool.format(
                name=project_agent_tool.name,
                description=project_agent_tool.description),
                metadata={"func_name": project_agent_tool.name,"tool_type":tool_type.value})
        
        
        self.projec_agent_tool_collection.add_documents(documents=[document],ids=[tool_id])
        self.logger.info(f"Tool/Agent {project_agent_tool.name} added to the collection.")
    
        
    
    def get_tool_to_resolve_query(self,query:str,tools:Dict[str,StructuredTool],tool_type:ToolType=ToolType.Project)->StructuredTool:
        finalQuery = f"Which tool/agent should I use to respond to the query: \"{query}\""
        similarity_search_result = self.projec_agent_tool_collection.similarity_search_with_score(
            finalQuery,
            len(tools),
            filter={"tool_type": tool_type.value}
            )
        # print("Similarity Search Result",similarity_search_result)
        
        if not similarity_search_result:
            self.logger.debug(f"No Relevant tools found to Resolve query: '{query}'")
            return []
        
        allowed_tools = [doc for doc,score in similarity_search_result if round(score,1)==round(similarity_search_result[0][1],1)]
        self.logger.debug(f"{len(allowed_tools)} Relevant tools found to Resolve query: '{query}'")
        
        return [tools[tool_.metadata["func_name"]] for tool_ in allowed_tools]


if __name__ == "__main__":
    persistent_client = PersistentClient()
    embedding_function = OllamaEmbeddings(model="nomic-embed-text:latest")
    embedder = DocEmbedder(persistent_client,embedding_function)
    embedder.embedd_project_from_dir(
        r"C:\Users\roshan.yadav\13thWonder\the_special_nine_day\Github\Auto_Dictionary_database_creator_tool"
    )
    embedder.embedd_project_from_dir(
        r"C:\Users\roshan.yadav\13thWonder\the_special_nine_day\Github\Plant-monitoring-system"
    )
