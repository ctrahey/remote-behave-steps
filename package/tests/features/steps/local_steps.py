"""Local When/Then steps that verify state against the test server."""

import os
import requests
from behave import when, then

SERVER_BASE = os.environ.get("REMOTE_STEPS_SERVER", "http://localhost:9876/openapi.yaml")
# Strip the spec filename to get the base URL
if SERVER_BASE.endswith((".yaml", ".yml", ".json")):
    SERVER_BASE = SERVER_BASE.rsplit("/", 1)[0]


@when("I request the to-do list")
def step_request_todo_list(context):
    resp = requests.get(f"{SERVER_BASE}/todos", timeout=5)
    resp.raise_for_status()
    context.todo_list = resp.json()


@then('I should see {count:d} items')
def step_should_see_items(context, count):
    assert len(context.todo_list) == count, (
        f"Expected {count} items, got {len(context.todo_list)}: {context.todo_list}"
    )


@then('the list should include "{title}"')
def step_list_should_include(context, title):
    titles = [t["title"] for t in context.todo_list]
    assert title in titles, f"'{title}' not found in {titles}"


@then('the item "{title}" should have a description')
def step_item_should_have_description(context, title):
    for item in context.todo_list:
        if item["title"] == title:
            assert item.get("description"), f"Item '{title}' has no description"
            return
    raise AssertionError(f"Item '{title}' not found")
