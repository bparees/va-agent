#!/bin/bash

# Ask Red Hat Agent Wrapper Startup Script

echo "Starting Ask Red Hat Agent Wrapper..."
echo "=================================="

# Check if JWT token is set
if [ -z "$ARH_JWT_TOKEN" ]; then
    echo "⚠️  Warning: ARH_JWT_TOKEN environment variable is not set"
    echo "   The server will return 401 errors for chat requests"
    echo "   Set ARH_JWT_TOKEN before starting the server:"
    echo "   export ARH_JWT_TOKEN='your-jwt-token-here'"
    echo
fi

# Display configuration
echo "Configuration:"
echo "  ARH_BASE_URL: ${ARH_BASE_URL:-http://localhost:8000 (default)}"
echo "  ARH_APP_SOURCE_ID: ${ARH_APP_SOURCE_ID:-IFD-001 (default)}"
echo "  JWT Token: ${ARH_JWT_TOKEN:+configured}${ARH_JWT_TOKEN:-not set}"
echo

# Start the server
echo "Starting server on http://0.0.0.0:8000..."
echo "Press Ctrl+C to stop"
echo

python3 main.py
