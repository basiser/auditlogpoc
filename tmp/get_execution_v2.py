import requests
import json
from requests.auth import HTTPBasicAuth

username = "T003388R11-mcpuser"
password = "fdrL726J$mDKaJYCReR9Jt^DcyNk6E"
execution_id = "T003388R11-0000001783739237299-0-1"
mcp_id = "T003388R11-0000001783608634965-0-1"
base_url = "https://amer.autopilot.cloud.sap"

# Endpoint 1
print("=== Endpoint 1: GET /api/v1/executions/{id} ===")
try:
    r = requests.get(
        f"{base_url}/api/v1/executions/{execution_id}",
        auth=HTTPBasicAuth(username, password),
        headers={"Accept": "application/json"},
        timeout=30
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2) if r.text else "Empty response")
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Endpoint 2
print("=== Endpoint 2: GET /api/v1/mcp/{mcpId}/executions/{id} ===")
try:
    r = requests.get(
        f"{base_url}/api/v1/mcp/{mcp_id}/executions/{execution_id}",
        auth=HTTPBasicAuth(username, password),
        headers={"Accept": "application/json"},
        timeout=30
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2) if r.text else "Empty response")
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Endpoint 3: with output
print("=== Endpoint 3: GET /api/v1/executions/{id}?includeOutput=true ===")
try:
    r = requests.get(
        f"{base_url}/api/v1/executions/{execution_id}",
        auth=HTTPBasicAuth(username, password),
        headers={"Accept": "application/json"},
        params={"includeOutput": "true"},
        timeout=30
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2) if r.text else "Empty response")
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Endpoint 4: try with expand
print("=== Endpoint 4: GET /api/v1/executions/{id}?$expand=outputValues ===")
try:
    r = requests.get(
        f"{base_url}/api/v1/executions/{execution_id}",
        auth=HTTPBasicAuth(username, password),
        headers={"Accept": "application/json"},
        params={"$expand": "outputValues"},
        timeout=30
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2) if r.text else "Empty response")
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Endpoint 5: try with details
print("=== Endpoint 5: GET /api/v1/executions/{id}/details ===")
try:
    r = requests.get(
        f"{base_url}/api/v1/executions/{execution_id}/details",
        auth=HTTPBasicAuth(username, password),
        headers={"Accept": "application/json"},
        timeout=30
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2) if r.text else "Empty response")
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Endpoint 6: try with output
print("=== Endpoint 6: GET /api/v1/executions/{id}/output ===")
try:
    r = requests.get(
        f"{base_url}/api/v1/executions/{execution_id}/output",
        auth=HTTPBasicAuth(username, password),
        headers={"Accept": "application/json"},
        timeout=30
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2) if r.text else "Empty response")
except Exception as e:
    print(f"Error: {e}")
