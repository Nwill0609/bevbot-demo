# BevBot — Databricks Agent Bricks Demo

A fully functional multi-agent AI demo built on **Databricks Agent Bricks** for a fictional beverage company. BevBot shows how a Supervisor Agent can orchestrate multiple specialized sub-agents — each backed by a different Databricks capability — to handle a realistic operations workflow end-to-end.

---

## What This Demo Shows

The demo tells a single connected story across 4 steps, each routing to a different underlying technology:

| Step | Ask BevBot... | Under the hood |
|------|--------------|----------------|
| 1 | "What flavor is trending right now?" | **Knowledge Assistant** (RAG over a Q4 2025 trend report stored in a UC Volume) |
| 2 | "We're out of Guava — what's a similar flavor profile?" | **Vector Search** (semantic similarity over flavor embeddings in a Delta table) |
| 3 | "What does our supplier charge for Hibiscus? SKU HB-001, 50000 ml" | **UC Function** (Python function that calls a mock supplier pricing API) |
| 4 | "Order 50 liters of Hibiscus. SKU HB-001, ingredient ID ING004, 50000 ml" | **UC Function** (writes a confirmed purchase order to a Delta table) |

The Supervisor Agent figures out which sub-agent to call for each question — the user just types naturally.

---

## Architecture

```
User (chat UI)
    │
    ▼
Databricks App  ─────────────────────────────────────────────┐
(React + FastAPI)                                             │
    │                                                         │
    ▼                                                         │
Supervisor Agent  (mas-979cea15-endpoint)                    │
    │                                                         │
    ├── flavor-trend-bot ──────────── Knowledge Assistant     │
    │                                 └── UC Volume (RAG)     │
    │                                                         │
    ├── function-find-similar-flavors ─ UC Function           │
    │                                  └── Vector Search index│
    │                                                         │
    ├── function-check-supplier-price ─ UC Function           │
    │                                  └── mock supplier API  │
    │                                                         │
    ├── function-place-order ──────── UC Function             │
    │                                 └── orders Delta table  │
    │                                                         │
    ├── agent-inventory-genie ──────── Genie Space            │
    │                                  └── inventory Delta    │
    │                                      table (DBSQL)      │
    └── agent-recipe-genie ─────────── Genie Space            │
                                       └── recipes Delta      │
                                           table (DBSQL)      │
```

### Databricks capabilities demonstrated

- **Agent Bricks Supervisor Agent** — orchestrates routing across all sub-agents without hardcoded logic
- **Knowledge Assistant** — RAG pipeline over unstructured documents (the trend report), no custom code
- **Vector Search** — semantic similarity search over Delta table embeddings
- **Unity Catalog Functions** — Python tool-calling functions registered in UC, callable by any agent
- **Genie Spaces** — natural language → SQL over Delta tables, surfaced as an agent
- **Databricks Apps** — full-stack React + FastAPI app deployed natively on Databricks

---

## What's in This Repo

```
bevbot/
├── README.md                    ← You are here
├── DEMO.md                      ← Step-by-step redeployment guide
├── TASKS.md                     ← Full task log with all resource IDs from original deployment
│
├── q4_2025_flavor_trends.txt    ← Market trend report (uploaded to UC Volume for RAG)
├── setup_data.py                ← Creates all Delta tables (inventory, flavors, orders, recipes)
├── setup_vector_search.py       ← Creates Vector Search endpoint + flavor embedding index
├── setup_uc_functions.py        ← Registers UC functions (find_similar_flavors, check_supplier_price, place_order)
│
└── app/                         ← Databricks App source
    ├── app.yaml                 ← App config (command, serving endpoint resource)
    ├── app.py                   ← FastAPI entry point, serves SPA + /api routes
    ├── requirements.txt         ← Python dependencies
    ├── server/
    │   └── chat.py              ← /api/chat endpoint — calls Supervisor Agent, parses response
    └── frontend/
        ├── src/
        │   ├── App.tsx          ← Chat UI with starter prompts and message history
        │   └── components/      ← ChatMessage, ChatInput components
        └── (dist/ built locally, not committed — run `npm run build` before deploying)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | Databricks Agent Bricks (Supervisor Agent) |
| RAG / Knowledge | Databricks Knowledge Assistant |
| Semantic search | Databricks Vector Search |
| Tool calling | Unity Catalog Python functions |
| Structured data queries | Databricks Genie (AI/BI) |
| Storage | Delta Lake (Unity Catalog) |
| App frontend | React + TypeScript + Vite |
| App backend | FastAPI + Databricks SDK |
| App hosting | Databricks Apps |

---

## Live Demo

**Chat app:** https://bevbot-demo-7474657176218782.aws.databricksapps.com
**Supervisor Agent Playground:** https://fevm-bevbot-demo.cloud.databricks.com/ml/playground?endpoints=mas-979cea15-endpoint

> The playground supports the full 6-step story including Genie (inventory lookup + recipe generation). The app currently supports 4 steps — Genie steps require user-token OBO configuration not yet set up in the app.

---

## Redeploying

See [DEMO.md](DEMO.md) for the full step-by-step redeployment guide.

The short version:
1. Run the 3 setup scripts against a new workspace + catalog
2. Create the Knowledge Assistant, Genie spaces, and Supervisor Agent in the UI (manual — no API yet)
3. Update `SUPERVISOR_ENDPOINT` in `app/server/chat.py` with the new endpoint name
4. `cd app/frontend && npm install && npm run build`
5. Sync + deploy the app via `databricks apps deploy`
6. Grant the app service principal `CAN_QUERY` on the supervisor and KA endpoints
