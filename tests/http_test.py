import tasksflow.task
from loguru import logger
import asyncio
import aiohttp
import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def index():
    return {"message": "Hello World"}


@app.get("/items")
def items():
    return [1, 2, 3]


@app.get("/items/{item_id}")
def item(item_id: int):
    return {"item_id": item_id, "description": "This is an item"}


def test_http():
    uvicorn.run(app, host="0.0.0.0", port=8080)