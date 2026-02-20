# BevBot — AgentBricks Demo

A 4-step beverage operations demo built on Databricks Agent Bricks, showing a Supervisor Agent orchestrating Knowledge Assistant (RAG), Vector Search, and Unity Catalog functions.

---

## Demo Story

Ask BevBot (via chat UI or Supervisor Agent Playground) in sequence:

1. **"What flavor is trending right now?"** — KA reads Q4 2025 trend report via RAG
2. **"We're out of Guava — what's a similar flavor profile?"** — Vector Search on flavor embeddings
3. **"What does our supplier charge for Hibiscus? Use SKU HB-001 and quantity 50000 ml"** — UC function calls mock supplier API
4. **"Order 50 liters of Hibiscus. SKU is HB-001, ingredient ID is ING004, quantity is 50000 ml"** — UC function writes to orders table

---

## Redeployment Guide

### Prerequisites

- Databricks workspace with **Agent Bricks** (Supervisor Agent) preview enabled
- **`agents_obo`** preview flag enabled (via Account Console → Preview Features)
- Unity Catalog enabled
- Serverless compute available
- Databricks CLI authenticated: `databricks auth login <workspace_url> --profile=<profile>`

### Step 1 — Data Setup

```bash
databricks fs cp bevbot/q4_2025_flavor_trends.txt \
  dbfs:/Volumes/bevbot_demo_catalog/inventory/raw/q4_2025_flavor_trends.txt \
  --profile=<profile>

databricks jobs run-now --job-id ... # or run setup_data.py as a notebook/job
```

Run the setup scripts in order:

| Script | What it creates |
|--------|----------------|
| `setup_data.py` | Delta tables: `inventory.stock`, `inventory.recipes`, `orders.purchase_orders`, `flavors.flavor_profiles` |
| `setup_vector_search.py` | VS endpoint `bevbot-flavor-search` + index `bevbot_demo_catalog.flavors.flavor_index` |
| `setup_uc_functions.py` | UC functions: `find_similar_flavors`, `check_supplier_price`, `place_order` |

Upload `q4_2025_flavor_trends.txt` to a UC Volume before running setup_data.py.

### Step 2 — Knowledge Assistant

Create a new Knowledge Assistant agent in the Databricks UI:
- Point it at the UC Volume containing `q4_2025_flavor_trends.txt`
- Name it `flavor-trend-bot`
- Note the endpoint name (`ka-XXXXXXXX-endpoint`)

### Step 3 — Genie Spaces

Create two Genie spaces in the Databricks UI:
- **Inventory Genie**: connect to `bevbot_demo_catalog.inventory.stock`
- **Recipe Genie**: connect to `bevbot_demo_catalog.inventory.recipes`

Note the Genie Room IDs.

### Step 4 — Supervisor Agent

Create a new Supervisor Agent in the Agent Bricks UI with these 6 sub-agents:

| Name | Type | Source |
|------|------|--------|
| `flavor-trend-bot` | Agent Endpoint | KA endpoint from Step 2 |
| `agent-inventory-genie` | Genie Space | Inventory Genie from Step 3 |
| `agent-recipe-genie` | Genie Space | Recipe Genie from Step 3 |
| `function-find-similar-flavors` | UC Function | `bevbot_demo_catalog.flavors.find_similar_flavors` |
| `function-check-supplier-price` | UC Function | `bevbot_demo_catalog.orders.check_supplier_price` |
| `function-place-order` | UC Function | `bevbot_demo_catalog.orders.place_order` |

Note the Supervisor Agent endpoint name (`mas-XXXXXXXX-endpoint`).

### Step 5 — Databricks App

Update `app/server/chat.py` — replace `SUPERVISOR_ENDPOINT` with the new endpoint name.

```bash
# Build frontend
cd app/frontend && npm install && npm run build

# Upload to workspace
databricks workspace mkdirs /Workspace/Users/<email>/bevbot-demo --profile=<profile>
databricks sync ./app /Workspace/Users/<email>/bevbot-demo --profile=<profile> --full

# Upload dist (gitignored, must build first)
databricks workspace mkdirs /Workspace/Users/<email>/bevbot-demo/frontend/dist/assets --profile=<profile>
databricks workspace import /Workspace/Users/<email>/bevbot-demo/frontend/dist/index.html \
  --file app/frontend/dist/index.html --format=AUTO --overwrite --profile=<profile>
databricks workspace import /Workspace/Users/<email>/bevbot-demo/frontend/dist/assets/<bundle>.js \
  --file app/frontend/dist/assets/<bundle>.js --format=AUTO --overwrite --profile=<profile>

# Create + deploy app
databricks apps create bevbot-demo --profile=<profile>
databricks apps deploy bevbot-demo \
  --source-code-path /Workspace/Users/<email>/bevbot-demo \
  --profile=<profile>
```

### Step 6 — Grant App Permissions

The app's service principal (from `databricks apps get bevbot-demo`) needs:

```bash
# Serving endpoints
PATCH /api/2.0/permissions/serving-endpoints/<supervisor-id>  → CAN_QUERY
PATCH /api/2.0/permissions/serving-endpoints/<ka-id>          → CAN_QUERY

# Unity Catalog
GRANT USE CATALOG ON CATALOG bevbot_demo_catalog TO `<sp-client-id>`;
GRANT USE SCHEMA, SELECT ON SCHEMA bevbot_demo_catalog.inventory TO `<sp-client-id>`;
GRANT USE SCHEMA, SELECT ON SCHEMA bevbot_demo_catalog.orders TO `<sp-client-id>`;
GRANT USE SCHEMA, SELECT ON SCHEMA bevbot_demo_catalog.flavors TO `<sp-client-id>`;
GRANT EXECUTE ON FUNCTION bevbot_demo_catalog.flavors.find_similar_flavors TO `<sp-client-id>`;
GRANT EXECUTE ON FUNCTION bevbot_demo_catalog.orders.check_supplier_price TO `<sp-client-id>`;
GRANT EXECUTE ON FUNCTION bevbot_demo_catalog.orders.place_order TO `<sp-client-id>`;

# Genie spaces (app-spaces permission type)
PATCH /api/2.0/permissions/app-spaces/<inventory-genie-id>  → CAN_MANAGE
PATCH /api/2.0/permissions/app-spaces/<recipe-genie-id>     → CAN_MANAGE

# Warehouse
PATCH /api/2.0/permissions/warehouses/<warehouse-id>  → CAN_USE
```

---

## Files in This Repo

```
bevbot/
├── DEMO.md                  ← This file
├── TASKS.md                 ← Full task log with all IDs/URLs from original deployment
├── q4_2025_flavor_trends.txt
├── setup_data.py
├── setup_vector_search.py
├── setup_uc_functions.py
└── app/                     ← Databricks App source (React + FastAPI)
    ├── app.yaml
    ├── app.py
    ├── requirements.txt
    ├── pyproject.toml
    ├── server/
    │   └── chat.py          ← Update SUPERVISOR_ENDPOINT constant when redeploying
    └── frontend/
        ├── src/             ← React source
        └── (dist/ built locally, not committed)
```

> **TASKS.md** contains all resource IDs, URLs, and endpoint names from the original deployment — use it as a reference if recreating in the same workspace.
