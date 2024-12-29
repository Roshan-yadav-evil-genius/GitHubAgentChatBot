from omegaconf import OmegaConf
from git_hub_project_loader import GitHubProjectLoader
from doc_embedder import DocEmbedder
from langchain_core.tools import tool
from langchain_core.tools import StructuredTool
from chromadb import PersistentClient
from langchain_ollama import OllamaEmbeddings
from typing import Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    ToolCall,
)
from rich import print
import logging
from langchain_chroma import Chroma
from utils.loaded_project import LoadedProject
from utils.tool_call import ToolCallModel
from prompt_loader import PromptLoader
from utils.structured_tool_input import ProjectAgentInput,ProjectHubAgentInput

config = OmegaConf.load("config.yaml")


class AutonomousAgent:

    def __init__(self):
        """Initialize only if it's the first instance"""
        self.logger = logging.getLogger(__name__)
        self.project_loader = GitHubProjectLoader()
        self.persistent_client = PersistentClient()
        self.embedding_function = OllamaEmbeddings(model="nomic-embed-text:latest")
        self.project_embedder = DocEmbedder(
            self.persistent_client, self.embedding_function
        )
        self.model = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
        self.available_tools: Dict[str, StructuredTool] = {}
        self.prompt_loader = PromptLoader()

    def run(self):
        loaded_projects: List[LoadedProject] = self.project_loader.load_projects()

        for loaded_project in loaded_projects:
            self.project_embedder.generate_embeddings_if_absent(loaded_project)
            project_agent_tool: StructuredTool = self.initialize_project_agent_tool(
                loaded_project
            )
            self.available_tools.setdefault(project_agent_tool.name, project_agent_tool)

    @property
    def project_hub_agent(self) -> StructuredTool:
        agent = StructuredTool.from_function(
            func=self._project_hub_agent,
            name="project_hub_agent",
            description="Provides assistance in resolving queries about various projects developed by the user.",
            args_schema=ProjectHubAgentInput,
        )
        return agent

    def _project_hub_agent(self, query: str) -> str:

        chat_prompt = self.prompt_loader.load_chat("project_hub_agent")

        chat_history = chat_prompt.invoke({"query": query}).to_messages()

        tools = self.project_embedder.get_tool_to_resolve_query(
            query, self.available_tools
        )

        model = self.model.bind_tools(tools)

        result: AIMessage = model.invoke(chat_history)
        chat_history.append(result)

        if not result.tool_calls:
            print(chat_history)
            return result

        for tool_call in result.tool_calls:
            tool_result: ToolMessage = self._perform_tool_call(tool_call)
            chat_history.append(tool_result)

        result: AIMessage = model.invoke(chat_history)
        chat_history.append(result)

        print(chat_history)
        return result

    def _perform_tool_call(self, tool_call: ToolCall) -> ToolMessage:
        tool_call = ToolCallModel(**tool_call)
        tool_instance = self.available_tools[tool_call.name]
        tool_raw_result = tool_instance.invoke(tool_call.args)
        return ToolMessage(tool_raw_result, tool_call_id=tool_call.id)

    def _project_agent(self, embedding_collection_name: str, query: str) -> str:
        self.logger.info(
            f"Project Agent '{embedding_collection_name}' invoked with {query=}"
        )
        vector_store = Chroma(
            client=self.persistent_client,
            collection_name=embedding_collection_name,
            embedding_function=self.embedding_function,
            create_collection_if_not_exists=False,
        )

        similarity_search_result = vector_store.similarity_search(query, k=4)
        context = "\n\n".join(
            [f"{doc.page_content}" for doc in similarity_search_result]
        )

        prompt = self.prompt_loader.load_template("project_agent")
        messages = prompt.invoke({"question": query, "context": context})
        resp = self.model.invoke(messages)

        return resp.content

    def initialize_project_agent_tool(self, loaded_project: LoadedProject):

        project = self.prompt_loader.load_template("project_agent_tool_description")

        project_agent_tool = StructuredTool.from_function(
            func=lambda query: self._project_agent(loaded_project.name, query),
            name=loaded_project.agent_name,
            description=project.format(
                name=loaded_project.path.name, about=loaded_project.about
            ),
            args_schema=ProjectAgentInput,
        )

        self.project_embedder.embed_tool_if_missing(project_agent_tool)
        return project_agent_tool


if __name__ == "__main__":
    agent = AutonomousAgent()
    agent.run()
    agent.project_hub_agent.invoke(
        "Could you please provide a brief overview of the Auto Database Creator tool? Additionally, could you list the packages used in this project?"
    )
