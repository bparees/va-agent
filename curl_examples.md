# Curl Examples with Authentication

## 1. Test Agent Discovery

```bash
curl -X GET http://localhost:8080/v1/agents \
  -H "Authorization: Bearer arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c"
```

## 2. Test Chat (Non-streaming)

```bash
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c" \
  -H "X-IBM-Thread-ID: test-thread-123" \
  -d '{
    "messages": [
      {"role": "user", "content": "How do I install Docker on RHEL 9?"}
    ],
    "stream": false
  }'
```

## 3. Test Chat (Streaming)

```bash
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c" \
  -H "X-IBM-Thread-ID: test-thread-456" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is Red Hat Enterprise Linux?"}
    ],
    "stream": true
  }'
```

## 4. Test Conversation Continuity (Second message in same thread)

```bash
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c" \
  -H "X-IBM-Thread-ID: test-thread-123" \
  -d '{
    "messages": [
      {"role": "user", "content": "What are the system requirements for that?"}
    ],
    "stream": false
  }'
```

## Authentication Notes

- **Required**: All endpoints now require a Bearer token in the Authorization header
- **Default Token**: `arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c`
- **Custom Token**: Set via `AGENT_BEARER_TOKEN` environment variable
- **Error Response**: Returns 401 Unauthorized with `WWW-Authenticate: Bearer` header if token is missing or invalid

## Testing Authentication

```bash
# This will fail with 401
curl -X GET http://localhost:8080/v1/agents

# This will fail with 401
curl -X GET http://localhost:8080/v1/agents \
  -H "Authorization: Bearer wrong-token"

# This will succeed with 200
curl -X GET http://localhost:8080/v1/agents \
  -H "Authorization: Bearer arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c"
```
