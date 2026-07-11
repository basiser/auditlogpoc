#!/bin/bash

# Endpoint 1: Direct execution endpoint
echo "=== Endpoint 1: GET /api/v1/executions/{id} ==="
curl -s -u "T003388R11-mcpuser:fdrL726J\$mDKaJYCReR9Jt^DcyNk6E" \
  "https://amer.autopilot.cloud.sap/api/v1/executions/T003388R11-0000001783739237299-0-1" \
  -H "Accept: application/json"

echo ""
echo ""

# Endpoint 2: MCP-scoped execution endpoint
echo "=== Endpoint 2: GET /api/v1/mcp/{mcpId}/executions/{id} ==="
curl -s -u "T003388R11-mcpuser:fdrL726J\$mDKaJYCReR9Jt^DcyNk6E" \
  "https://amer.autopilot.cloud.sap/api/v1/mcp/T003388R11-0000001783608634965-0-1/executions/T003388R11-0000001783739237299-0-1" \
  -H "Accept: application/json"

echo ""
echo ""

# Endpoint 3: Try with output parameter
echo "=== Endpoint 3: GET /api/v1/executions/{id}?includeOutput=true ==="
curl -s -u "T003388R11-mcpuser:fdrL726J\$mDKaJYCReR9Jt^DcyNk6E" \
  "https://amer.autopilot.cloud.sap/api/v1/executions/T003388R11-0000001783739237299-0-1?includeOutput=true" \
  -H "Accept: application/json"
