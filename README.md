# Red Hat Console Agent Wrapper

This server wraps the Red Hat Console Virtual Assistant API and provides an Agent Connect compatible interface for interacting with Red Hat's AI assistant.

## Features

- Agent Connect compatible API endpoints (`/v1/agents` and `/v1/chat`)
- Streaming and non-streaming responses (streaming is simulated for the Red Hat Console API)
- Direct integration with Red Hat Console Virtual Assistant API
- Comprehensive error handling and logging

## Configuration

The server requires the following environment variables:

### Required
- `ARH_JWT_TOKEN`: JWT token for authenticating with the Red Hat Console API (same askRH token used elsewhere)

### Optional
- `AGENT_BEARER_TOKEN`: Bearer token required for client authentication (default: `arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c`)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export ARH_JWT_TOKEN="your-jwt-token-here"
```

## Running the Server

```bash
python main.py
```

The server will start on `http://0.0.0.0:8000` by default.

## API Endpoints

### GET /v1/agents
Returns information about the available Red Hat Console agent.

### POST /v1/chat
Send a chat message to the Red Hat Console Virtual Assistant API.

**Headers:**
- `Authorization`: Bearer token (required)
- `X-IBM-Thread-ID` (optional): Thread identifier for conversation continuity

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "How do I configure SELinux in RHEL 9?"}
  ],
  "stream": true
}
```

**Response:**
- Streaming: Server-Sent Events format with incremental response chunks
- Non-streaming: Complete response with thread_id, conversation_id, and response content

## Usage Example

```python
import requests
import json

# Set up authentication
headers = {"Authorization": "Bearer arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c"}

# Agent discovery
agents = requests.get("http://localhost:8000/v1/agents", headers=headers).json()
print(f"Available agents: {agents}")

# Send a chat message
response = requests.post(
    "http://localhost:8000/v1/chat",
    headers={
        "Authorization": "Bearer arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c",
        "X-IBM-Thread-ID": "test-thread-123"
    },
    json={
        "messages": [{"role": "user", "content": "How do I install Docker on RHEL?"}],
        "stream": False
    }
)
print(f"Response: {response.json()}")
```

## Integration with Red Hat Console API

This wrapper:
1. Directly calls the Red Hat Console Virtual Assistant API at `https://console.redhat.com/api/virtual-assistant-v2/v2/talk`
2. Forwards user queries to the API with the format `{"input":{"text":"$userquery"}}`
3. Uses the same askRH JWT token for authentication
4. Simulates streaming responses for compatibility (Red Hat Console API doesn't support streaming)

## Error Handling

The server provides comprehensive error handling for:
- Missing JWT token configuration
- Failed Red Hat Console API connections
- Invalid responses from the API
- Network connection issues

All errors are logged and appropriate HTTP status codes are returned.

## Development

For development:
1. Set the `ARH_JWT_TOKEN` environment variable to your askRH JWT token
2. The API endpoint is hardcoded to the Red Hat Console API
3. Check the server logs for troubleshooting API responses

## Dependencies

- FastAPI: Web framework
- uvicorn: ASGI server
- requests: HTTP client for backend communication
- pydantic: Data validation and serialization
