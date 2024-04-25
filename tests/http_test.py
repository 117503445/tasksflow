import tasksflow.task
from loguru import logger
import asyncio
import aiohttp
import uvicorn
from fastapi import FastAPI
import pytest
from aiohttp import web
import json
import requests
import tasksflow.cache

routes = web.RouteTableDef()

db_items = {
    1: {"description": "This is an item"},
    2: {"description": "This is another item"},
}


def make_response(data):
    return web.Response(text=json.dumps(data), content_type="application/json")


@routes.get("/")
async def index(request: web.Request):
    return make_response({"message": "Hello World"})


@routes.get("/items")
async def items(request: web.Request):
    return make_response(list(db_items.keys()))


@routes.get("/items/{item_id}")
async def item(request: web.Request):
    item_id = request.match_info["item_id"]
    return make_response(
        {"item_id": item_id, "description": db_items[int(item_id)]["description"]}
    )


app = web.Application()
app.add_routes(routes)


class Task1(tasksflow.task.Task):
    def run(self):
        resp = requests.get("http://localhost:18080/items")
        return {"items_list_resp": resp.json()}


class Task2(tasksflow.task.Task):
    def run(self, items_list_resp: dict):
        descriptions = []
        for item_id in items_list_resp:
            resp = requests.get(f"http://localhost:18080/items/{item_id}")
            descriptions.append(resp.json()["description"])

        return {"descriptions": descriptions}


stop_event = asyncio.Event()


@pytest.mark.asyncio
async def test_http():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 18080)
    await site.start()

    p = tasksflow.task.Pool(
        [Task1(), Task2()], cache_provider=tasksflow.cache.MemoryCacheProvider()
    )
    loop = asyncio.get_running_loop()

    def _run():
        result = p.run()
        logger.debug(f"result: {result}")
        stop_event.set()

    loop.run_in_executor(None, _run)
    try:
        await stop_event.wait()
    finally:
        await runner.cleanup()
