"""
BevBot Demo — Vector Search Setup
Creates the Vector Search endpoint and synced index over flavor_profiles.
"""
import subprocess
import json
import time

PROFILE = "fe-vm-bevbot-demo"
CATALOG = "bevbot_demo_catalog"
ENDPOINT_NAME = "bevbot-flavor-search"
INDEX_NAME = f"{CATALOG}.flavors.flavor_index"
SOURCE_TABLE = f"{CATALOG}.flavors.flavor_profiles"


def api(method: str, path: str, payload: dict = None) -> dict:
    args = ["databricks", "api", method, path, "--profile", PROFILE]
    if payload:
        args += ["--json", json.dumps(payload)]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  API error: {result.stderr.strip()}")
        return {}
    return json.loads(result.stdout) if result.stdout.strip() else {}


def wait_for_endpoint(name: str, timeout_min: int = 15) -> bool:
    print(f"  Waiting for endpoint '{name}' to be ONLINE...", end="", flush=True)
    for _ in range(timeout_min * 4):
        resp = api("get", f"/api/2.0/vector-search/endpoints/{name}")
        state = resp.get("endpoint_status", {}).get("state", "")
        if state == "ONLINE":
            print(" ONLINE")
            return True
        if state in ("OFFLINE", ""):
            pass
        print(".", end="", flush=True)
        time.sleep(15)
    print(" TIMEOUT")
    return False


def wait_for_index(full_index_name: str, timeout_min: int = 20) -> bool:
    encoded = full_index_name.replace(".", "%2E")
    print(f"  Waiting for index to be ONLINE...", end="", flush=True)
    for _ in range(timeout_min * 4):
        resp = api("get", f"/api/2.0/vector-search/indexes/{encoded}")
        state = resp.get("status", {}).get("detailed_state", "")
        if state in ("ONLINE", "ONLINE_NO_PENDING_UPDATE"):
            print(f" {state}")
            return True
        if "FAIL" in state:
            print(f" FAILED: {state}")
            return False
        print(".", end="", flush=True)
        time.sleep(15)
    print(" TIMEOUT")
    return False


def main():
    print("\n=== BevBot — Vector Search Setup ===\n")

    # 1. Create endpoint
    print("1. Creating Vector Search endpoint...")
    existing = api("get", f"/api/2.0/vector-search/endpoints/{ENDPOINT_NAME}")
    if existing.get("name"):
        print(f"  Endpoint '{ENDPOINT_NAME}' already exists.")
    else:
        resp = api("post", "/api/2.0/vector-search/endpoints", {
            "name": ENDPOINT_NAME,
            "endpoint_type": "STANDARD"
        })
        if not resp:
            print("  Failed to create endpoint.")
            return
        print(f"  Created endpoint: {ENDPOINT_NAME}")

    if not wait_for_endpoint(ENDPOINT_NAME):
        print("  Endpoint did not come online. Exiting.")
        return

    # 2. Create delta-sync index
    print("\n2. Creating Vector Search index over flavor_profiles...")
    encoded_index = INDEX_NAME.replace(".", "%2E")
    existing_idx = api("get", f"/api/2.0/vector-search/indexes/{encoded_index}")
    if existing_idx.get("name"):
        print(f"  Index '{INDEX_NAME}' already exists.")
    else:
        resp = api("post", "/api/2.0/vector-search/indexes", {
            "name": INDEX_NAME,
            "endpoint_name": ENDPOINT_NAME,
            "primary_key": "flavor_id",
            "index_type": "DELTA_SYNC",
            "delta_sync_index_spec": {
                "source_table": SOURCE_TABLE,
                "pipeline_type": "TRIGGERED",
                "embedding_source_columns": [
                    {
                        "name": "flavor_text",
                        "embedding_model_endpoint_name": "databricks-gte-large-en"
                    }
                ]
            }
        })
        if not resp:
            print("  Failed to create index.")
            return
        print(f"  Created index: {INDEX_NAME}")

    wait_for_index(INDEX_NAME)

    print("\n✅ Vector Search setup complete!")
    print(f"  Endpoint: {ENDPOINT_NAME}")
    print(f"  Index:    {INDEX_NAME}")
    print(f"  Source:   {SOURCE_TABLE}")


if __name__ == "__main__":
    main()
