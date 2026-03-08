"""Local When/Then steps — these run in your test process, not remotely.

The recommended pattern is:
  - Given steps: remote (set up fixtures on the service under test)
  - When/Then steps: local (drive and assert against the service's public API)
"""

import os

import requests
from behave import then, when

# In a real project, this would be your service's API base URL.
SERVER_BASE = os.environ.get("TODO_SERVICE_URL", "http://localhost:9876")


@when("I request the to-do list")
def step_request_todo_list(context):
    resp = requests.get(f"{SERVER_BASE}/todos", timeout=5)
    resp.raise_for_status()
    context.todo_list = resp.json()


@then("I should see {count:d} items")
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
