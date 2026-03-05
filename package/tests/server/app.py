"""Example remote steps server for integration testing.

A simple to-do management service with in-memory state.
Implements the remote_behave_steps meta-API specification.
"""

from flask import Flask, jsonify, request
import yaml

app = Flask(__name__)

# Global in-memory state
state = {"todos": []}


OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Test Todo Service",
        "version": "1.0.0",
        "x-behave-spec-version": "1.0",
    },
    "paths": {
        "/healthz": {
            "get": {
                "summary": "Health check",
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/reset-all-data": {
            "put": {
                "summary": "Reset all data",
                "responses": {"200": {"description": "Reset complete"}},
            },
        },
        "/hooks/before-scenario": {
            "put": {
                "summary": "Before scenario hook",
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/hooks/after-scenario": {
            "put": {
                "summary": "After scenario hook",
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/existing-todos": {
            "put": {
                "summary": "Create N generic to-do items",
                "x-behave-pattern": 'I have "{count}" existing to-do items',
                "responses": {"200": {"description": "Created"}},
            },
        },
        "/todo-with-title": {
            "put": {
                "summary": "Create a to-do with a specific title",
                "x-behave-pattern": 'a to-do item titled "{title}"',
                "responses": {"200": {"description": "Created"}},
            },
        },
        "/todo-items": {
            "put": {
                "summary": "Create to-do items from a table",
                "x-behave-pattern": "the following to-do items exist",
                "responses": {"200": {"description": "Created"}},
            },
        },
        "/todo-with-description": {
            "put": {
                "summary": "Create a to-do with a multiline description",
                "x-behave-pattern": 'a to-do item titled "{title}" with description',
                "responses": {"200": {"description": "Created"}},
            },
        },
    },
}


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.get("/openapi.yaml")
def openapi_spec():
    return yaml.dump(OPENAPI_SPEC), 200, {"Content-Type": "text/yaml"}


@app.put("/reset-all-data")
def reset_all_data():
    state["todos"] = []
    return jsonify({"status": "ok"})


@app.put("/hooks/before-scenario")
def before_scenario():
    # Could set up per-scenario state; for now just acknowledge
    return jsonify({"status": "ok"})


@app.put("/hooks/after-scenario")
def after_scenario():
    return jsonify({"status": "ok"})


@app.put("/existing-todos")
def existing_todos():
    body = request.json
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
    return jsonify({"status": "ok", "data": {"created_ids": created_ids}})


@app.put("/todo-with-title")
def todo_with_title():
    body = request.json
    title = body["inputs"]["title"]
    todo_id = len(state["todos"]) + 1
    state["todos"].append({
        "id": todo_id,
        "title": title,
        "priority": "medium",
        "description": "",
    })
    return jsonify({"status": "ok", "data": {"id": todo_id}})


@app.put("/todo-items")
def todo_items():
    body = request.json
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
    return jsonify({"status": "ok", "data": {"created_ids": created_ids}})


@app.put("/todo-with-description")
def todo_with_description():
    body = request.json
    title = body["inputs"]["title"]
    description = body["inputs"].get("text", "")
    todo_id = len(state["todos"]) + 1
    state["todos"].append({
        "id": todo_id,
        "title": title,
        "priority": "medium",
        "description": description,
    })
    return jsonify({"status": "ok", "data": {"id": todo_id}})


# Read-only endpoint for test assertions (not a remote step)
@app.get("/todos")
def get_todos():
    return jsonify(state["todos"])
