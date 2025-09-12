import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request, Response, Header, HTTPException, Depends
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
import json
import time
import uuid
import asyncio
from datetime import datetime, timezone
from pydantic import BaseModel
import requests
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Request/Response logging middleware
class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log incoming request
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]
        
        # Log request details (without consuming body for streaming compatibility)
        logger.info(f"[{request_id}] INCOMING REQUEST")
        logger.info(f"[{request_id}] Method: {request.method}")
        logger.info(f"[{request_id}] URL: {request.url}")
        logger.info(f"[{request_id}] Path: {request.url.path}")
        logger.info(f"[{request_id}] Query Params: {dict(request.query_params)}")
        logger.info(f"[{request_id}] Headers: {dict(request.headers)}")
        
        # Only read body for non-streaming requests to avoid conflicts
        content_type = request.headers.get("content-type", "")
        if request.method in ["POST", "PUT", "PATCH"] and "application/json" in content_type:
            try:
                # Try to peek at body without consuming it fully
                body = await request.body()
                if body:
                    try:
                        body_json = json.loads(body.decode('utf-8'))
                        logger.info(f"[{request_id}] Body (JSON): {json.dumps(body_json, indent=2)}")
                        
                        # Recreate request with body for FastAPI to process
                        async def receive():
                            return {"type": "http.request", "body": body, "more_body": False}
                        request._receive = receive
                        
                    except json.JSONDecodeError:
                        logger.info(f"[{request_id}] Body (raw): {body.decode('utf-8', errors='replace')[:500]}...")
                else:
                    logger.info(f"[{request_id}] Body: (empty)")
            except Exception as e:
                logger.warning(f"[{request_id}] Could not read request body: {e}")
        else:
            logger.info(f"[{request_id}] Body: (not logged for this request type)")
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response details
            logger.info(f"[{request_id}] OUTGOING RESPONSE")
            logger.info(f"[{request_id}] Status Code: {response.status_code}")
            logger.info(f"[{request_id}] Headers: {dict(response.headers)}")
            logger.info(f"[{request_id}] Processing Time: {process_time:.3f}s")
            
            # Check response type
            if hasattr(response, 'body_iterator'):
                logger.info(f"[{request_id}] Response Type: Streaming")
            else:
                logger.info(f"[{request_id}] Response Type: Standard")
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"[{request_id}] REQUEST FAILED")
            logger.error(f"[{request_id}] Error: {str(e)}")
            logger.error(f"[{request_id}] Processing Time: {process_time:.3f}s")
            raise

# Initialize FastAPI app
app = FastAPI(title="Red Hat Console Agent Wrapper")

# Note: Middleware removed to avoid streaming conflicts - logging added directly to endpoints

# Define message schema
class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    stream: bool = False

# Red Hat Console API Client
class RedHatConsoleClient:
    def __init__(self, jwt_token: str = ""):
        self.api_url = "https://console.redhat.com/api/virtual-assistant-v2/v2/talk"
        self.jwt_token = jwt_token
        self.verify_ssl = True
        
    def _get_headers(self):
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
    
    async def send_message(self, message: str):
        """Send a message to the Red Hat Console API"""
        headers = self._get_headers()
        
        payload = {
            "input": {
                "text": message
            }
        }
        
        # Log outgoing request to Red Hat Console API
        logger.info("=== OUTGOING REQUEST TO RED HAT CONSOLE API ===")
        logger.info(f"Method: POST")
        logger.info(f"URL: {self.api_url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Body: {json.dumps(payload, indent=2)}")
        
        try:
            start_time = time.time()
            response = requests.post(self.api_url, headers=headers, json=payload, verify=self.verify_ssl)
            response_time = time.time() - start_time
            
            # Log response from Red Hat Console API
            logger.info("=== RESPONSE FROM RED HAT CONSOLE API ===")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Time: {response_time:.3f}s")
            logger.info(f"Response Headers: {dict(response.headers)}")
            logger.info(f"Response Body: {response.text}")
            
            return response
        except Exception as e:
            logger.error(f"✗ Error sending message: {str(e)}")
            return None

# Configuration from environment variables
ARH_JWT_TOKEN = os.getenv("ARH_JWT_TOKEN", "")

# Authentication configuration
REQUIRED_BEARER_TOKEN = os.getenv("AGENT_BEARER_TOKEN", "arh-agent-7f8e9d2c-4b6a-41e3-9f2d-8c7b5a4e1f9c")

# Initialize Red Hat Console client
rh_client = RedHatConsoleClient(ARH_JWT_TOKEN)

# Note: Red Hat Console API doesn't require conversation management

# Authentication dependency
def verify_bearer_token(authorization: str = Header(None)):
    """Verify the Bearer token in the Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Authorization header must start with 'Bearer '",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    if token != REQUIRED_BEARER_TOKEN:
        raise HTTPException(
            status_code=401, 
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return token

# Agent discovery endpoint
@app.get("/v1/agents")
async def discover_agents(token: str = Depends(verify_bearer_token)):
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] AGENT DISCOVERY REQUEST (authenticated)")
    
    response = {
        "agents": [
            {
                "name": "Red Hat Console Agent",
                "description": "Connects to the Red Hat Console Virtual Assistant API for Red Hat product assistance",
                "provider": {
                    "organization": "Red Hat",
                    "url": "https://redhat.com"
                },
                "version": "1.0.0",
                "documentation_url": "https://access.redhat.com",
                "capabilities": {
                    "streaming": True
                }
            }
        ]
    }
    
    logger.info(f"[{request_id}] Agent discovery response sent")
    return response

# Chat completion endpoint
@app.post("/v1/chat")
async def chat_completion(
    request: ChatRequest, 
    x_ibm_thread_id: str = Header(None),
    token: str = Depends(verify_bearer_token)
):
    thread_id = x_ibm_thread_id or str(uuid.uuid4())
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Log incoming chat request
    logger.info(f"[{request_id}] CHAT REQUEST (authenticated)")
    logger.info(f"[{request_id}] Thread ID: {thread_id}")
    logger.info(f"[{request_id}] Stream: {request.stream}")
    logger.info(f"[{request_id}] Messages: {json.dumps([msg for msg in request.messages], indent=2)}")
    
    # Check if JWT token is configured (optional - will be needed for actual Red Hat Console API calls)
    if not rh_client.jwt_token:
        logger.warning(f"[{request_id}] JWT token not configured - API calls to Red Hat Console will likely fail")
        # Continue anyway - let the Red Hat Console API return its own authentication error
    
    # Extract the user query from the messages - handle WatsonX Orchestrate format
    user_messages = [msg for msg in request.messages if msg["role"] == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # For WatsonX Orchestrate, look for the actual user question
    query = user_messages[-1]["content"]
    
    # Red Hat Console API doesn't support streaming, so we always use non-streaming
    logger.info(f"[{request_id}] Starting response (Red Hat Console API doesn't support streaming)")
    
    # Send message to Red Hat Console API
    response = await rh_client.send_message(query)
    if not response or response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to get response from Red Hat Console API")
    
    # Parse the response
    try:
        response_data = response.json()
        
        # Extract text from Red Hat Console API response format: 
        # {"response": [{"text": "...", "type": "TEXT|OPTIONS", "options": [...]}], ...}
        if (isinstance(response_data, dict) and 
            'response' in response_data and 
            isinstance(response_data['response'], list) and 
            len(response_data['response']) > 0 and 
            isinstance(response_data['response'][0], dict)):
            
            response_item = response_data['response'][0]
            response_content = response_item.get('text', 'No response text')
            
            # Handle OPTIONS type responses with selectable options
            if response_item.get('type') == 'OPTIONS' and 'options' in response_item:
                options = response_item['options']
                if options:
                    response_content += "\n\nOptions:"
                    for i, option in enumerate(options, 1):
                        option_text = option.get('text', f'Option {i}')
                        response_content += f"\n{i}. {option_text}"
        else:
            # Fallback - use the raw response
            response_content = str(response_data)
            
    except Exception as e:
        logger.error(f"[{request_id}] Error parsing response: {str(e)}")
        raise HTTPException(status_code=500, detail="Invalid response from Red Hat Console API")

    # Log and return response in appropriate format
    process_time = time.time() - start_time
    logger.info(f"[{request_id}] Response completed in {process_time:.3f}s")
    
    if request.stream:
        # Even though Red Hat Console API doesn't support streaming, we can simulate it
        # by sending the entire response as a single chunk
        logger.info(f"[{request_id}] Simulating streaming response")
        return StreamingResponse(
            simulate_streaming_response(response_content, request_id),
            media_type="text/event-stream"
        )
    else:
        # OpenAI-style chat completion format
        return {
            "id": f"chatcmpl-{str(uuid.uuid4())[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "red-hat-console-agent",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }
            ]
        }

async def simulate_streaming_response(response_content: str, request_id: str):
    """Simulate streaming response for Red Hat Console API (which doesn't support streaming)"""
    completion_id = f"chatcmpl-{str(uuid.uuid4())[:8]}"
    created_timestamp = int(time.time())
    
    try:
        logger.info(f"[{request_id}] Simulating streaming response")
        
        # Send the entire response as a single chunk
        chunk_response = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created_timestamp,
            "model": "red-hat-console-agent",
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": response_content},
                    "finish_reason": None
                }
            ]
        }
        yield f"data: {json.dumps(chunk_response)}\n\n"
        
        # Send final chunk with finish_reason
        final_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created_timestamp,
            "model": "red-hat-console-agent",
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield f"data: [DONE]\n\n"
        
        logger.info(f"[{request_id}] Simulated streaming response completed")
        
    except Exception as e:
        logger.error(f"[{request_id}] ✗ Error simulating streaming response: {str(e)}")
        error_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created_timestamp,
            "model": "red-hat-console-agent",
            "choices": [{"index": 0, "delta": {"content": f"Error: {str(e)}"}, "finish_reason": "stop"}]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield f"data: [DONE]\n\n"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
