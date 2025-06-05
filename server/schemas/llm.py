from pydantic import BaseModel

class LatexRequest(BaseModel):
    code: str
