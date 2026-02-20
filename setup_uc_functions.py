"""
BevBot Demo — Unity Catalog Functions Setup
Creates the three agent tool functions:
  1. find_similar_flavors  — wraps Vector Search, returns JSON string
  2. check_supplier_price  — mocks supplier REST API
  3. place_order           — returns order confirmation string
"""
import subprocess
import json
import time

PROFILE = "fe-vm-bevbot-demo"
CATALOG = "bevbot_demo_catalog"
WAREHOUSE_ID = "d1ce1d2fbb31ec7c"


def run_sql(statement: str, description: str = "") -> dict:
    if description:
        print(f"  → {description}")
    payload = json.dumps({
        "statement": statement,
        "warehouse_id": WAREHOUSE_ID,
        "catalog": CATALOG,
        "wait_timeout": "50s",
        "on_wait_timeout": "CONTINUE"
    })
    result = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/sql/statements",
         "--profile", PROFILE, "--json", payload],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"    ERROR: {result.stderr.strip()}")
        return {}
    resp = json.loads(result.stdout)
    state = resp.get("status", {}).get("state", "")
    if state == "RUNNING":
        stmt_id = resp.get("statement_id", "")
        resp = poll_statement(stmt_id)
        state = resp.get("status", {}).get("state", "")
    if state != "SUCCEEDED":
        print(f"    Status: {state}")
        err = resp.get("status", {}).get("error", {})
        if err:
            print(f"    Error: {err.get('message', '')}")
    return resp


def poll_statement(statement_id: str) -> dict:
    for _ in range(60):
        result = subprocess.run(
            ["databricks", "api", "get",
             f"/api/2.0/sql/statements/{statement_id}",
             "--profile", PROFILE],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {}
        resp = json.loads(result.stdout)
        state = resp.get("status", {}).get("state", "")
        if state in ("SUCCEEDED", "FAILED", "CANCELLED", "CLOSED"):
            return resp
        time.sleep(3)
    return {}


def main():
    print("\n=== BevBot — Unity Catalog Functions Setup ===\n")

    # ── Function 1: find_similar_flavors (returns STRING / JSON) ─────────────
    # Note: Python TVFs require a HANDLER class — simpler to return JSON string.
    print("1. Creating flavors.find_similar_flavors (returns JSON)...")
    sql1 = (
        "CREATE OR REPLACE FUNCTION " + CATALOG + """.flavors.find_similar_flavors(
  query_flavor STRING COMMENT 'The flavor or taste profile to search for similar matches',
  num_results  INT    COMMENT 'Number of similar flavors to return (default 4)'
)
RETURNS STRING
COMMENT 'Uses semantic vector search to find flavor profiles similar to the given input. Returns a JSON array of similar flavors with their taste descriptions. Use this when substituting an out-of-stock flavor or exploring taste alternatives.'
LANGUAGE PYTHON
AS $$
import json as _json
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient(disable_notice=True)
results = vsc.get_index(
    endpoint_name="bevbot-flavor-search",
    index_name=\"""" + CATALOG + """.flavors.flavor_index\\"
).similarity_search(
    query_text=query_flavor,
    columns=["flavor_id", "flavor_name", "flavor_text"],
    num_results=num_results if num_results else 4
)
rows = results.get("result", {}).get("data_array", [])
output = [{"flavor_id": r[0], "flavor_name": r[1], "description": r[2], "similarity_score": round(r[3], 4)} for r in rows]
return _json.dumps(output)
$$;"""
    )
    run_sql(sql1, "find_similar_flavors")

    # ── Function 2: check_supplier_price ─────────────────────────────────────
    print("\n2. Creating orders.check_supplier_price...")
    sql2 = (
        "CREATE OR REPLACE FUNCTION " + CATALOG + """.orders.check_supplier_price(
  supplier_sku   STRING  COMMENT 'The supplier SKU to look up pricing for',
  quantity_ml    DOUBLE  COMMENT 'Quantity in ml to get pricing for'
)
RETURNS STRUCT<
  unit_price_per_liter  DOUBLE,
  total_cost_usd        DOUBLE,
  available_quantity_ml DOUBLE,
  lead_time_days        INT,
  currency              STRING,
  in_stock              BOOLEAN
>
COMMENT 'Checks current price and availability from the supplier catalog API. Returns unit price per liter, total cost for the requested quantity, availability status, and estimated lead time in days.'
LANGUAGE PYTHON
AS $$
catalog = {
    "SUP-MNG-001": {"price": 12.50, "available": 50000, "lead_time": 3},
    "SUP-PAS-002": {"price": 18.75, "available": 30000, "lead_time": 5},
    "SUP-LYC-003": {"price": 24.00, "available": 20000, "lead_time": 7},
    "SUP-YUZ-004": {"price": 9.99,  "available": 60000, "lead_time": 2},
    "SUP-COC-005": {"price": 7.50,  "available": 80000, "lead_time": 2},
    "SUP-HIB-006": {"price": 15.00, "available": 25000, "lead_time": 4},
    "SUP-GUA-007": {"price": 16.50, "available": 35000, "lead_time": 5},
    "SUP-BLO-008": {"price": 8.25,  "available": 70000, "lead_time": 2},
}
info = catalog.get(supplier_sku, {"price": 20.00, "available": 0, "lead_time": 14})
qty_liters = (quantity_ml or 1000) / 1000.0
total = round(info["price"] * qty_liters, 2)
return (info["price"], total, float(info["available"]), info["lead_time"], "USD", info["available"] > 0)
$$;"""
    )
    run_sql(sql2, "check_supplier_price")

    # ── Function 3: place_order ───────────────────────────────────────────────
    print("\n3. Creating orders.place_order...")
    sql3 = (
        "CREATE OR REPLACE FUNCTION " + CATALOG + """.orders.place_order(
  ingredient_id   STRING  COMMENT 'The ingredient ID from inventory (e.g. ING002)',
  ingredient_name STRING  COMMENT 'Human-readable ingredient name',
  quantity_ml     DOUBLE  COMMENT 'Quantity to order in milliliters',
  supplier_sku    STRING  COMMENT 'Supplier SKU code for the ingredient',
  unit_price      DOUBLE  COMMENT 'Confirmed unit price per liter in USD'
)
RETURNS STRING
COMMENT 'Places a purchase order with the supplier. Returns a confirmation string with order ID, quantities, total cost, and estimated delivery date. Use this after checking supplier price and confirming the quantity with the user.'
LANGUAGE PYTHON
AS $$
import uuid
from datetime import datetime

order_id = "ORD-" + str(uuid.uuid4())[:8].upper()
total_cost = round((quantity_ml / 1000.0) * unit_price, 2)
qty_liters = round(quantity_ml / 1000.0, 1)

lines = [
    "ORDER CONFIRMED",
    "Order ID: " + order_id,
    "Ingredient: " + ingredient_name + " (" + ingredient_id + ")",
    "Quantity: " + str(int(quantity_ml)) + " ml (" + str(qty_liters) + " L)",
    "Unit Price: $" + str(unit_price) + "/L",
    "Total Cost: $" + str(total_cost) + " USD",
    "SKU: " + supplier_sku,
    "Estimated Delivery: 3-7 business days",
    "Order placed: " + datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
]
return "\\n".join(lines)
$$;"""
    )
    run_sql(sql3, "place_order")

    print("\n✅ All UC functions created!")
    print(f"\nFunctions registered:")
    print(f"  - {CATALOG}.flavors.find_similar_flavors")
    print(f"  - {CATALOG}.orders.check_supplier_price")
    print(f"  - {CATALOG}.orders.place_order")


if __name__ == "__main__":
    main()
