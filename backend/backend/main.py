from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(root_path="/api/v1")


class Question(BaseModel):
    question: str


@app.get("/")
def chat(question: Question) -> str: ...
