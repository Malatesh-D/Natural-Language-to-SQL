from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)

class SQLRequest(BaseModel):
    sql: str = Field(min_length=6, max_length=20000)
