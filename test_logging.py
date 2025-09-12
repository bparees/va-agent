#!/usr/bin/env python3
"""
Test script to demonstrate the comprehensive logging
"""

import requests
import json

def test_with_logging():
    base_url = "http://localhost:8000"
    
    print("Testing comprehensive logging...")
    print("=" * 60)
    
    # Test 1: Agent discovery
    print("\n1. Testing Agent Discovery:")
    try:
        response = requests.get(f"{base_url}/v1/agents")
        print(f"Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Chat request (will fail without JWT token, but will show logging)
    print("\n2. Testing Chat Request (will show request logging):")
    try:
        response = requests.post(
            f"{base_url}/v1/chat",
            headers={
                "Content-Type": "application/json",
                "X-IBM-Thread-ID": "test-logging-thread"
            },
            json={
                "messages": [
                    {"role": "user", "content": "Hello, this is a test message"}
                ],
                "stream": False
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Check your server logs to see comprehensive request/response logging!")
    print("The logs will show:")
    print("- All incoming request details (method, URL, headers, body)")
    print("- Processing time for each request")
    print("- All outgoing requests to Ask Red Hat backend")
    print("- All responses from Ask Red Hat backend")
    print("- Streaming chunk details (when streaming)")

if __name__ == "__main__":
    test_with_logging()
