"""Fake to-do service for the example project.

This is both the application under test (GET /todos) and the fixture
provider (PUT endpoints with x-behave-pattern). In a real system these
might be separate services; here they live together for simplicity.
"""

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import yaml

app = FastAPI(title="Test Todo Service", version="1.0.0")

# Global in-memory state
state = {"todos": []}


@app.get("/healthz", summary="Health check")
async def healthz():
    return {"status": "ok"}


@app.get("/openapi.yaml", summary="OpenAPI spec as YAML", include_in_schema=False)
async def openapi_yaml():
    return PlainTextResponse(yaml.dump(app.openapi()), media_type="text/yaml")


@app.put("/reset-all-data", summary="Reset all data")
async def reset_all_data():
    state["todos"] = []
    return {"status": "ok"}


@app.put("/hooks/before-scenario", summary="Before scenario hook")
async def before_scenario():
    state["todos"] = []
    return {"status": "ok"}


@app.put("/hooks/after-scenario", summary="After scenario hook")
async def after_scenario():
    return {"status": "ok"}


@app.put("/existing-todos", summary="Create N generic to-do items", openapi_extra={
    "x-behave-pattern": 'I have "{count}" existing to-do items',
    "x-behave-step-type": "given",
})
async def existing_todos(request: Request):
    body = await request.json()
    count = int(body["inputs"]["count"])
    created_ids = []
    for i in range(count):
        todo_id = len(state["todos"]) + 1
        state["todos"].append({
            "id": todo_id,
            "title": f"Todo item {todo_id}",
            "priority": "medium",
            "description": "",
        })
        created_ids.append(todo_id)
    return {"status": "ok", "data": {"created_ids": created_ids}}


@app.put("/todo-with-title", summary="Create a to-do with a specific title", openapi_extra={
    "x-behave-pattern": 'a to-do item titled "{title}"',
    "x-behave-step-type": "given",
})
async def todo_with_title(request: Request):
    body = await request.json()
    title = body["inputs"]["title"]
    todo_id = len(state["todos"]) + 1
    state["todos"].append({
        "id": todo_id,
        "title": title,
        "priority": "medium",
        "description": "",
    })
    return {"status": "ok", "data": {"id": todo_id}}


@app.put("/todo-items", summary="Create to-do items from a table", openapi_extra={
    "x-behave-pattern": "the following to-do items exist",
    "x-behave-step-type": "given",
})
async def todo_items(request: Request):
    body = await request.json()
    table = body["inputs"]["table"]
    headings = table["headings"]
    created_ids = []
    for row in table["rows"]:
        todo_id = len(state["todos"]) + 1
        item = {"id": todo_id}
        for heading, value in zip(headings, row):
            item[heading] = value
        state["todos"].append(item)
        created_ids.append(todo_id)
    return {"status": "ok", "data": {"created_ids": created_ids}}


@app.put("/todo-with-description", summary="Create a to-do with a multiline description", openapi_extra={
    "x-behave-pattern": 'a to-do item titled "{title}" with description',
    "x-behave-step-type": "given",
})
async def todo_with_description(request: Request):
    body = await request.json()
    title = body["inputs"]["title"]
    description = body["inputs"].get("text", "")
    todo_id = len(state["todos"]) + 1
    state["todos"].append({
        "id": todo_id,
        "title": title,
        "priority": "medium",
        "description": description,
    })
    return {"status": "ok", "data": {"id": todo_id}}


# Read-only endpoint for test assertions (not a remote step)
@app.get("/todos", summary="List all todos")
async def get_todos():
    return state["todos"]
