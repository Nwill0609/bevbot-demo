# BevBot AgentBricks Demo — Tasks

## Status: COMPLETE ✅ (App deployed)

---

## Workspace
- **URL:** https://fevm-bevbot-demo.cloud.databricks.com
- **Org ID:** 7474657176218782
- **Profile:** fe-vm-bevbot-demo
- **Catalog:** bevbot_demo_catalog

---

## Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create Delta tables (inventory, flavors, orders, recipes) | ✅ Done | `setup_data.py` |
| 2 | Upload flavor trends report to UC Volume | ✅ Done | `q4_2025_flavor_trends.txt` |
| 3 | Create Vector Search endpoint + flavor index | ✅ Done | Endpoint: `bevbot-flavor-search` (ONLINE), Index: `bevbot_demo_catalog.flavors.flavor_index` |
| 4 | Create UC functions (find_similar_flavors, check_supplier_price, place_order) | ✅ Done | `setup_uc_functions.py` |
| 5 | Build Knowledge Assistant (flavor-trend-bot) | ✅ Done | Endpoint: `ka-573a44cf-endpoint` (READY) |
| 6 | Create Inventory Genie Space | ✅ Done | Genie Room: `01f10dd85dcb151c8c169474266ba32b` |
| 7 | Create Recipe Genie Space | ✅ Done | Genie Room: `01f10dd8dbdc1af697946669717f9dbd` |
| 8 | Enable `agents_obo` preview flag | ✅ Done | User activated via Account Console |
| 9 | Build Supervisor Agent (bevbot-supervisor) | ✅ Done | SA ID: `979cea15-cb99-42c8-9fd6-f67348ca3609`, Endpoint: `mas-979cea15-endpoint` |
| 10 | Deploy Databricks App (chat UI) | ✅ Done | App: `bevbot-demo`, URL: `https://bevbot-demo-7474657176218782.aws.databricksapps.com`, source: `bevbot/app/` |

---

## Supervisor Agent Configuration

**Name:** `bevbot-supervisor`
**URL:** https://fevm-bevbot-demo.cloud.databricks.com/ml/bricks/sa/configure/979cea15-cb99-42c8-9fd6-f67348ca3609
**Playground:** https://fevm-bevbot-demo.cloud.databricks.com/ml/playground?endpoints=mas-979cea15-endpoint

### Sub-agents (6 total)

| Agent | Type | Source |
|-------|------|--------|
| `flavor-trend-bot` | Agent Endpoint | `ka-573a44cf-endpoint` |
| `agent-inventory-genie` | Genie Space | Inventory Genie |
| `agent-recipe-genie` | Genie Space | Recipe Genie |
| `function-find-similar-flavors` | UC Function | `bevbot_demo_catalog.flavors.find_similar_flavors` |
| `function-check-supplier-price` | UC Function | `bevbot_demo_catalog.orders.check_supplier_price` |
| `function-place-order` | UC Function | `bevbot_demo_catalog.orders.place_order` |

---

---

## Databricks App

**URL:** https://bevbot-demo-7474657176218782.aws.databricksapps.com
**Source:** `bevbot/app/` (React + FastAPI, port 8000)
**App name:** `bevbot-demo`

### App Demo Status

| Step | Prompt | Agent | Status |
|------|--------|-------|--------|
| 1 | "What flavor is trending right now?" | `flavor-trend-bot` (KA/RAG) | ✅ Working |
| 2 | "We're out of Guava — what's similar?" | `function-find-similar-flavors` (Vector Search) | ✅ Working |
| 3 | "How much Hibiscus do we have in stock?" | `agent-inventory-genie` (Genie) | ⚠️ Needs user-token OBO config |
| 4 | "What does supplier charge for Hibiscus? SKU HB-001, 50000ml" | `function-check-supplier-price` | ✅ Working |
| 5 | "Order 50L Hibiscus. SKU HB-001, ING004, 50000ml" | `function-place-order` | ✅ Working |
| 6 | "Give me 3 drink recipes using current inventory" | `agent-recipe-genie` (Genie) | ⚠️ Needs user-token OBO config |

**Note on Genie steps (3 & 6):** Genie spaces require the calling user's OAuth token (OBO). The app currently calls the supervisor agent using service principal M2M auth. To enable Genie in the app, configure it to forward the `X-Forwarded-Access-Token` header with the `model-serving` scope — OR use the Supervisor Agent Playground directly for full end-to-end demo (playground uses user credentials and all 6 steps work).

---

## Demo Story Flow

1. **"What flavor is trending right now?"** → `flavor-trend-bot` (KA / RAG over trend report)
2. **"We're out of that flavor — what's similar?"** → `function-find-similar-flavors` (Vector Search)
3. **"How much of [substitute] do we have in stock?"** → `agent-inventory-genie` (Genie / DBSQL)
4. **"What does the supplier charge for [substitute]?"** → `function-check-supplier-price` (mock supplier API)
5. **"Order 50L of [substitute]"** → `function-place-order` (UC function / tool calling)
6. **"Give me 3 drink recipes using what we have"** → `agent-recipe-genie` (Genie / DBSQL)
