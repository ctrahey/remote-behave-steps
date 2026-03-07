"""Fake retail catalog service for the full example project.

Implements all remote_behave_steps features: fixture endpoints, lifecycle
hooks, and a public API for test assertions. Demonstrates a realistic
service that manages products, categories, and inventory.
"""

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import yaml

app = FastAPI(title="Retail Catalog Service", version="1.0.0")

state = {
    "products": [],
    "categories": [],
    "hook_log": [],  # Track hook invocations for test assertions
}


# -- Health & spec endpoints --------------------------------------------------

@app.get("/healthz", summary="Health check")
async def healthz():
    return {"status": "ok"}


@app.get("/openapi.yaml", summary="OpenAPI spec as YAML", include_in_schema=False)
async def openapi_yaml():
    return PlainTextResponse(yaml.dump(app.openapi()), media_type="text/yaml")


# -- Lifecycle endpoints (reset + hooks) --------------------------------------

@app.put("/reset-all-data", summary="Reset all data")
async def reset_all_data():
    state["products"] = []
    state["categories"] = []
    state["hook_log"] = []
    return {"status": "ok"}


@app.put("/hooks/before-all", summary="Before all hook")
async def before_all(request: Request):
    body = await request.json()
    state["hook_log"].append({"hook": "before_all", "run_id": body.get("run_id")})
    return {"status": "ok"}


@app.put("/hooks/after-all", summary="After all hook")
async def after_all(request: Request):
    body = await request.json()
    state["hook_log"].append({"hook": "after_all", "run_id": body.get("run_id")})
    return {"status": "ok"}


@app.put("/hooks/before-feature", summary="Before feature hook")
async def before_feature(request: Request):
    body = await request.json()
    state["hook_log"].append({
        "hook": "before_feature",
        "feature": body.get("feature", {}).get("name"),
    })
    return {"status": "ok"}


@app.put("/hooks/after-feature", summary="After feature hook")
async def after_feature(request: Request):
    body = await request.json()
    state["hook_log"].append({
        "hook": "after_feature",
        "feature": body.get("feature", {}).get("name"),
    })
    return {"status": "ok"}


@app.put("/hooks/before-scenario", summary="Before scenario hook")
async def before_scenario(request: Request):
    body = await request.json()
    state["products"] = []
    state["categories"] = []
    state["hook_log"].append({
        "hook": "before_scenario",
        "scenario": body.get("scenario", {}).get("name"),
    })
    return {"status": "ok"}


@app.put("/hooks/after-scenario", summary="After scenario hook")
async def after_scenario(request: Request):
    body = await request.json()
    state["hook_log"].append({
        "hook": "after_scenario",
        "scenario": body.get("scenario", {}).get("name"),
    })
    return {"status": "ok"}


@app.put("/hooks/before-step", summary="Before step hook")
async def before_step(request: Request):
    body = await request.json()
    state["hook_log"].append({
        "hook": "before_step",
        "step": body.get("step", {}).get("text"),
    })
    return {"status": "ok"}


@app.put("/hooks/after-step", summary="After step hook")
async def after_step(request: Request):
    body = await request.json()
    state["hook_log"].append({
        "hook": "after_step",
        "step": body.get("step", {}).get("text"),
    })
    return {"status": "ok"}


# -- Fixture endpoints (Given steps) ------------------------------------------

@app.put("/catalog-products", summary="Add products to the catalog", openapi_extra={
    "x-behave-pattern": 'the catalog has "{count}" products',
    "x-behave-step-type": "given",
})
async def catalog_products(request: Request):
    body = await request.json()
    count = int(body["inputs"]["count"])
    created_ids = []
    for i in range(count):
        product_id = len(state["products"]) + 1
        state["products"].append({
            "id": product_id,
            "name": f"Product {product_id}",
            "price": 9.99,
            "category": "general",
            "in_stock": True,
        })
        created_ids.append(product_id)
    return {"status": "ok", "data": {"created_ids": created_ids}}


@app.put("/product-with-name", summary="Add a named product", openapi_extra={
    "x-behave-pattern": 'a product named "{name}" at ${price}',
    "x-behave-step-type": "given",
})
async def product_with_name(request: Request):
    body = await request.json()
    product_id = len(state["products"]) + 1
    state["products"].append({
        "id": product_id,
        "name": body["inputs"]["name"],
        "price": float(body["inputs"]["price"]),
        "category": "general",
        "in_stock": True,
    })
    return {"status": "ok", "data": {"id": product_id}}


@app.put("/products-from-table", summary="Add products from a table", openapi_extra={
    "x-behave-pattern": "the following products exist",
    "x-behave-step-type": "given",
})
async def products_from_table(request: Request):
    body = await request.json()
    table = body["inputs"]["table"]
    headings = table["headings"]
    created_ids = []
    for row in table["rows"]:
        product_id = len(state["products"]) + 1
        item = {"id": product_id, "in_stock": True}
        for heading, value in zip(headings, row):
            if heading == "price":
                item[heading] = float(value)
            else:
                item[heading] = value
        state["products"].append(item)
        created_ids.append(product_id)
    return {"status": "ok", "data": {"created_ids": created_ids}}


@app.put("/category", summary="Add a category with description", openapi_extra={
    "x-behave-pattern": 'a category "{name}" with description',
    "x-behave-step-type": "given",
})
async def category_with_description(request: Request):
    body = await request.json()
    category_id = len(state["categories"]) + 1
    state["categories"].append({
        "id": category_id,
        "name": body["inputs"]["name"],
        "description": body["inputs"].get("text", ""),
    })
    return {"status": "ok", "data": {"id": category_id}}


# -- Deliberately broken endpoints (for error-handling tests) -----------------

@app.put("/broken-server-error", summary="Endpoint that crashes", openapi_extra={
    "x-behave-pattern": "the server has an internal error",
    "x-behave-step-type": "given",
})
async def broken_server_error(request: Request):
    raise RuntimeError("Simulated infrastructure failure")


@app.put("/broken-validation", summary="Endpoint that rejects input", openapi_extra={
    "x-behave-pattern": "the server rejects the request",
    "x-behave-step-type": "given",
})
async def broken_validation(request: Request):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=422,
        content={"error": {"message": "Invalid product data: missing required field 'name'"}},
    )


@app.put("/broken-logic-error", summary="Endpoint that returns a logical error", openapi_extra={
    "x-behave-pattern": "the server reports a logical error",
    "x-behave-step-type": "given",
})
async def broken_logic_error(request: Request):
    return {
        "status": "error",
        "error": {"message": "Cannot add product: category does not exist"},
    }


# -- Public API (for When/Then steps) -----------------------------------------

@app.get("/products", summary="List all products")
async def get_products():
    return state["products"]


@app.get("/categories", summary="List all categories")
async def get_categories():
    return state["categories"]


@app.get("/hooks-log", summary="View hook invocation log")
async def get_hooks_log():
    return state["hook_log"]
