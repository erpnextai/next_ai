from pydantic import BaseModel, Field
from typing import List


class NEXTAIBaseModel(BaseModel):
    content = Field(..., description="Generate content based on the input provided.")