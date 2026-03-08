"""Local When/Then steps for the retail catalog example."""

import os

import requests
from behave import then, when

SERVER_BASE = os.environ.get("CATALOG_SERVICE_URL", "http://localhost:9877")


@when("I browse the product catalog")
def step_browse_catalog(context):
    resp = requests.get(f"{SERVER_BASE}/products", timeout=5)
    resp.raise_for_status()
    context.product_list = resp.json()


@when("I browse the categories")
def step_browse_categories(context):
    resp = requests.get(f"{SERVER_BASE}/categories", timeout=5)
    resp.raise_for_status()
    context.category_list = resp.json()


@when("I check the hooks log")
def step_check_hooks_log(context):
    resp = requests.get(f"{SERVER_BASE}/hooks-log", timeout=5)
    resp.raise_for_status()
    context.hooks_log = resp.json()


@then("I should see {count:d} products")
def step_should_see_products(context, count):
    assert len(context.product_list) == count, (
        f"Expected {count} products, got {len(context.product_list)}"
    )


@then('the catalog should include "{name}"')
def step_catalog_should_include(context, name):
    names = [p["name"] for p in context.product_list]
    assert name in names, f"'{name}' not found in {names}"


@then('"{name}" should cost ${price}')
def step_product_should_cost(context, name, price):
    for p in context.product_list:
        if p["name"] == name:
            assert p["price"] == float(price), f"Expected ${price}, got ${p['price']}"
            return
    raise AssertionError(f"Product '{name}' not found")


@then("I should see {count:d} categories")
def step_should_see_categories(context, count):
    assert len(context.category_list) == count, (
        f"Expected {count} categories, got {len(context.category_list)}"
    )


@then('the category "{name}" should have a description')
def step_category_should_have_description(context, name):
    for c in context.category_list:
        if c["name"] == name:
            assert c.get("description"), f"Category '{name}' has no description"
            return
    raise AssertionError(f"Category '{name}' not found")


@then('the hooks log should include a "{hook}" entry')
def step_hooks_log_should_include(context, hook):
    hooks = [entry["hook"] for entry in context.hooks_log]
    assert hook in hooks, f"'{hook}' not found in hooks log: {hooks}"
