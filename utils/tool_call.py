from pydantic import BaseModel
from typing import Any, Optional

class ToolCallModel(BaseModel):
    name: str
    args: dict[str, Any]
    id: Optional[str] = None
    type: Optional[str] = None