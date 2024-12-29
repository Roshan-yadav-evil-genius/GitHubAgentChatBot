from pydantic import BaseModel,field_validator,model_validator
from pathlib import Path
from rich import print

class LoadedProject(BaseModel):
    name:str
    path:Path
    about:str=None
    
    @property
    def agent_name(self):
        return self.name + "_project_agent"
    
    @field_validator("name")
    def process_name(cls, value):
        return value.lower().replace(" ","_").replace("-","_")
    
    @model_validator(mode="before")
    def process_about(cls, fields):
        description_file_path = Path(fields['path']) / "project.description"
        if description_file_path.exists():
            with open(description_file_path, "r") as description_file:
                fields['about'] =  description_file.read()
        return fields


if __name__=="__main__":
    loaded_project = LoadedProject(name="My Project",path=Path(r"C:\Users\roshan.yadav\13thWonder\the_special_nine_day\Github\Auto_Dictionary_database_creator_tool"))
    print(loaded_project)
    print(loaded_project.agent_name)
