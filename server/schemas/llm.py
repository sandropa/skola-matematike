from pydantic import BaseModel

class LatexRequest(BaseModel):
    code: str

class MathImageRequest(BaseModel):
    image_bytes: bytes
    mime_type: str
