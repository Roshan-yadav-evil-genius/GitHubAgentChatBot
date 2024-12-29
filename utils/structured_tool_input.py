from pydantic import BaseModel,Field

class ProjectAgentInput(BaseModel):
    query: str = Field(description="A specific query related to the project.")


class ProjectHubAgentInput(BaseModel):
    query: str = Field(
        description="A specific question or inquiry related to the user's projects."
    )