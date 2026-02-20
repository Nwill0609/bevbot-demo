"""
BevBot Demo — Data Setup Script
Runs all SQL via the Databricks SQL Statement API against the serverless warehouse.
"""
import subprocess
import json
import time
import sys

PROFILE = "fe-vm-bevbot-demo"
WAREHOUSE_ID = "d1ce1d2fbb31ec7c"
CATALOG = "bevbot_demo_catalog"

def poll_statement(statement_id: str) -> dict:
    """Poll a running SQL statement until it completes."""
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


def run_sql(statement: str, description: str = "") -> dict:
    """Execute a SQL statement via the Databricks CLI and wait for completion."""
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
        print(f"    ERROR: {result.stderr}")
        return {}
    resp = json.loads(result.stdout)
    state = resp.get("status", {}).get("state", "UNKNOWN")
    # If still running, poll until done
    if state == "RUNNING":
        stmt_id = resp.get("statement_id", "")
        if stmt_id:
            resp = poll_statement(stmt_id)
            state = resp.get("status", {}).get("state", "UNKNOWN")
    if state != "SUCCEEDED":
        print(f"    Status: {state}")
        err = resp.get("status", {}).get("error", {})
        if err:
            print(f"    Error: {err.get('message', '')}")
    return resp


def main():
    print("\n=== BevBot Demo — Data Setup ===\n")

    # ── Schemas ──────────────────────────────────────────────────────────────
    print("1. Creating schemas...")
    for schema in ["inventory", "flavors", "orders"]:
        run_sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{schema}",
                f"Schema: {CATALOG}.{schema}")

    # ── Inventory stock table ────────────────────────────────────────────────
    print("\n2. Creating inventory.stock table...")
    run_sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.inventory.stock (
  ingredient_id        STRING,
  ingredient_name      STRING,
  flavor_profile       STRING,
  category             STRING,
  quantity_ml          DOUBLE,
  reorder_threshold_ml DOUBLE,
  cost_per_liter       DOUBLE,
  supplier_sku         STRING,
  last_updated         TIMESTAMP
)
""", "CREATE TABLE inventory.stock")

    run_sql(f"""
INSERT INTO {CATALOG}.inventory.stock VALUES
  ('ING001','Mango Syrup',        'tropical, sweet, fruity',   'syrup',   2500, 5000, 12.50,'SUP-MNG-001',current_timestamp()),
  ('ING002','Passion Fruit Puree','tropical, tart, exotic',    'puree',   1200, 3000, 18.75,'SUP-PAS-002',current_timestamp()),
  ('ING003','Lychee Extract',     'floral, sweet, delicate',   'extract',  800, 2000, 24.00,'SUP-LYC-003',current_timestamp()),
  ('ING004','Yuzu Juice',         'citrus, tart, aromatic',    'juice',   3000, 4000,  9.99,'SUP-YUZ-004',current_timestamp()),
  ('ING005','Coconut Cream',      'creamy, sweet, tropical',   'cream',   5000, 6000,  7.50,'SUP-COC-005',current_timestamp()),
  ('ING006','Hibiscus Syrup',     'floral, tart, earthy',      'syrup',    400, 2500, 15.00,'SUP-HIB-006',current_timestamp()),
  ('ING007','Guava Puree',        'tropical, sweet, musky',    'puree',    300, 3000, 16.50,'SUP-GUA-007',current_timestamp()),
  ('ING008','Blood Orange Juice', 'citrus, bitter, tangy',     'juice',   6000, 5000,  8.25,'SUP-BLO-008',current_timestamp())
""", "INSERT 8 ingredients")

    # ── Orders table ─────────────────────────────────────────────────────────
    print("\n3. Creating orders.purchase_orders table...")
    run_sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.orders.purchase_orders (
  order_id        STRING,
  ingredient_id   STRING,
  ingredient_name STRING,
  quantity_ml     DOUBLE,
  unit_price      DOUBLE,
  total_cost      DOUBLE,
  supplier_sku    STRING,
  status          STRING,
  ordered_at      TIMESTAMP
)
""", "CREATE TABLE orders.purchase_orders")

    # ── Recipes table ─────────────────────────────────────────────────────────
    print("\n4. Creating inventory.recipes table...")
    run_sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.inventory.recipes (
  recipe_id      STRING,
  recipe_name    STRING,
  ingredients    STRING,
  instructions   STRING,
  flavor_notes   STRING,
  prep_time_min  INT
)
""", "CREATE TABLE inventory.recipes")

    run_sql(f"""
INSERT INTO {CATALOG}.inventory.recipes VALUES
  ('R001','Tropical Sunset',
   'Mango Syrup, Passion Fruit Puree, Coconut Cream',
   'Shake 30ml mango syrup, 20ml passion fruit puree, 40ml coconut cream with ice. Strain into glass.',
   'Sweet, tropical, creamy', 5),
  ('R002','Yuzu Spritz',
   'Yuzu Juice, Hibiscus Syrup',
   'Mix 40ml yuzu juice with 20ml hibiscus syrup, top with sparkling water.',
   'Citrus, floral, refreshing', 3),
  ('R003','Lychee Cloud',
   'Lychee Extract, Coconut Cream',
   'Blend 25ml lychee extract with 50ml coconut cream and crushed ice.',
   'Floral, sweet, creamy', 4),
  ('R004','Guava Sunrise',
   'Guava Puree, Blood Orange Juice, Coconut Cream',
   'Layer 40ml guava puree and 30ml blood orange juice, float 20ml coconut cream on top.',
   'Tropical, citrus, creamy', 5),
  ('R005','Mango Hibiscus Cooler',
   'Mango Syrup, Hibiscus Syrup',
   'Mix 25ml mango syrup and 15ml hibiscus syrup, top with sparkling water and ice.',
   'Sweet, floral, refreshing', 3)
""", "INSERT 5 recipes")

    # ── Flavor profiles table (for Vector Search) ────────────────────────────
    print("\n5. Creating flavors.flavor_profiles table (for Vector Search)...")
    run_sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.flavors.flavor_profiles (
  flavor_id   STRING,
  flavor_name STRING,
  flavor_text STRING,
  category    STRING
) TBLPROPERTIES (delta.enableChangeDataFeed = true)
""", "CREATE TABLE flavors.flavor_profiles")

    run_sql(f"""
INSERT INTO {CATALOG}.flavors.flavor_profiles VALUES
  ('F001','Mango',        'tropical sweet fruity stone fruit warm golden sunny',       'fruit'),
  ('F002','Passion Fruit','tropical tart exotic acidic vibrant orange zingy',          'fruit'),
  ('F003','Lychee',       'floral sweet delicate perfumed soft white subtle',          'fruit'),
  ('F004','Yuzu',         'citrus tart aromatic bright Japanese zesty fresh',          'citrus'),
  ('F005','Coconut',      'creamy sweet tropical nutty mild white smooth',             'cream'),
  ('F006','Hibiscus',     'floral tart earthy ruby red tangy botanical',               'botanical'),
  ('F007','Guava',        'tropical sweet musky pink dense lush',                      'fruit'),
  ('F008','Blood Orange', 'citrus bitter tangy deep red bold punchy',                  'citrus'),
  ('F009','Pineapple',    'tropical sweet acidic bright golden spiky juicy',           'fruit'),
  ('F010','Tamarind',     'sweet sour tangy tropical brown dense complex',             'botanical'),
  ('F011','Peach',        'stone fruit sweet floral soft peachy gentle warm',          'fruit'),
  ('F012','Strawberry',   'berry sweet fruity red bright familiar classic',            'fruit')
""", "INSERT 12 flavor profiles")

    # ── UC Volume for trend docs ─────────────────────────────────────────────
    print("\n6. Creating UC Volume for trend documents...")
    run_sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.content", "Schema: content")
    run_sql(f"""
CREATE EXTERNAL VOLUME IF NOT EXISTS {CATALOG}.content.trend_docs
""", "Try external volume (may fail - will use managed)")
    # Try managed volume as fallback
    run_sql(f"""
CREATE VOLUME IF NOT EXISTS {CATALOG}.content.trend_docs
""", "CREATE VOLUME content.trend_docs (managed)")

    print("\n✅ All tables and schemas created successfully!")
    print(f"\nWorkspace:  https://fevm-bevbot-demo.cloud.databricks.com")
    print(f"Catalog:    {CATALOG}")
    print(f"Tables created:")
    print(f"  - {CATALOG}.inventory.stock        (8 ingredients)")
    print(f"  - {CATALOG}.inventory.recipes      (5 drink recipes)")
    print(f"  - {CATALOG}.orders.purchase_orders (empty, ready for orders)")
    print(f"  - {CATALOG}.flavors.flavor_profiles (12 flavors for vector search)")
    print(f"  - Volume: {CATALOG}.content.trend_docs (for trend report docs)")


if __name__ == "__main__":
    main()
