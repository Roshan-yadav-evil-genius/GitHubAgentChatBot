from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
from omegaconf import OmegaConf
from pathlib import Path
from utils.errors import PromptTemplateNotFoundError,ChatTemplateNotFoundError
from rich import print

class PromptLoader:
    def load_chat(self,chat_name:str)->ChatPromptTemplate:
        # current directorie + Prompts + Chat + chat_name.yaml
        chat_path = Path(__file__).parent / "Prompts" / "Chats" / f"{chat_name}.yaml"
        
        if chat_path.exists() == False:
            raise ChatTemplateNotFoundError(f"Unable to locate the chat template '{chat_path}'. Please verify that the name is correct.")
        
        config = OmegaConf.load(chat_path)
        return ChatPromptTemplate(list(map(lambda d: (d['role'], d['content']), config.chat)))

        

    
    def load_template(self,template_name:str)-> PromptTemplate:
        template_path = Path(__file__).parent / "Prompts" / f"templates.yaml"
        config = OmegaConf.load(template_path)
        
        if template_name not in config:
            raise PromptTemplateNotFoundError(f"Unable to locate the prompt template '{template_name}'. Please ensure it is included in the '{template_path}' or verify that the name is correct.")
        
        return PromptTemplate.from_template(config[template_name])



if __name__ == "__main__":
    print(PromptLoader().load_chat("project_hub_agent").invoke(dict(query="What is the project about?")))
    print(PromptLoader().load_template("project_agent"))