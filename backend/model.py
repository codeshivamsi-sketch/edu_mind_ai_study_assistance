from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str

class AgentRequest(BaseModel):
    question: str