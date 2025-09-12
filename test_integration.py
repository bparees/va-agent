#!/usr/bin/env python3
"""
Test script for Red Hat Console Agent Wrapper
"""

import requests
import json
import os
import sys

def test_agent_discovery(base_url):
    """Test the agent discovery endpoint"""
    print("Testing agent discovery...")
    try:
        response = requests.get(f"{base_url}/v1/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✓ Agent discovery successful: {agents['agents'][0]['name']}")
            return True
        else:
            print(f"✗ Agent discovery failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Agent discovery error: {str(e)}")
        return False

def test_chat_non_streaming(base_url, message="How do I install Docker on RHEL?"):
    """Test non-streaming chat"""
    print("Testing non-streaming chat...")
    try:
        response = requests.post(
            f"{base_url}/v1/chat",
            headers={"X-IBM-Thread-ID": "test-thread-123"},
            json={
                "messages": [{"role": "user", "content": message}],
                "stream": False
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Non-streaming chat successful")
            print(f"  Thread ID: {data.get('thread_id')}")
            print(f"  Messages count: {len(data.get('messages', []))}")
            if data.get('messages') and len(data['messages']) > 0:
                latest_message = data['messages'][-1]
                if latest_message.get('content'):
                    print(f"  Response preview: {latest_message['content'][:100]}...")
            return True
        else:
            print(f"✗ Non-streaming chat failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Non-streaming chat error: {str(e)}")
        return False

def test_chat_streaming(base_url, message="What is Red Hat Enterprise Linux?"):
    """Test streaming chat"""
    print("Testing streaming chat...")
    try:
        response = requests.post(
            f"{base_url}/v1/chat",
            headers={"X-IBM-Thread-ID": "test-thread-456"},
            json={
                "messages": [{"role": "user", "content": message}],
                "stream": True
            },
            stream=True
        )
        if response.status_code == 200:
            print("✓ Streaming chat initiated")
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        if data_str == '[DONE]':
                            print(f"  Streaming completed ({chunk_count} chunks received)")
                            break
                        elif data_str.startswith('{"error"'):
                            print(f"✗ Streaming error: {data_str}")
                            return False
                        else:
                            chunk_count += 1
                            if chunk_count <= 3:  # Show first few chunks
                                print(f"  Chunk {chunk_count}: {data_str[:50]}...")
            return True
        else:
            print(f"✗ Streaming chat failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Streaming chat error: {str(e)}")
        return False

def main():
    """Main test function"""
    base_url = os.getenv("TEST_BASE_URL", "http://localhost:8000")
    
    print("=" * 60)
    print("Red Hat Console Agent Wrapper Integration Test")
    print("=" * 60)
    print(f"Testing against: {base_url}")
    print()
    
    # Check if JWT token is configured
    jwt_token = os.getenv("ARH_JWT_TOKEN")
    if not jwt_token:
        print("⚠️  Warning: ARH_JWT_TOKEN not set. Some tests may fail.")
        print("   Set ARH_JWT_TOKEN environment variable before running tests.")
        print()
    
    # Run tests
    tests = [
        ("Agent Discovery", lambda: test_agent_discovery(base_url)),
        ("Non-Streaming Chat", lambda: test_chat_non_streaming(base_url)),
        ("Streaming Chat", lambda: test_chat_streaming(base_url)),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"✗ {total - passed} tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
