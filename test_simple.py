#!/usr/bin/env python3
"""
Simple test script for Wag-Tail AI Gateway OSS Edition
Tests basic functionality: health, plugins, and chat endpoints
"""

import requests
import json
import time
import sys

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "demo-key-for-testing"  # Use the demo key from README

def test_health():
    """Test health endpoint"""
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed: {data['status']}")
            print(f"   Edition: {data.get('edition', 'unknown')}")
            return True
        else:
            print(f"   ❌ Health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_plugins():
    """Test plugins endpoint"""
    print("\n2. Testing Plugins Endpoint...")
    try:
        response = requests.get(f"{API_URL}/plugins")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Plugins loaded: {data['total_plugins']}")
            print(f"   Edition: {data['edition']}")
            for plugin in data.get('plugins', []):
                print(f"      - {plugin['name']}")
            return True
        else:
            print(f"   ❌ Plugins check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Plugins check error: {e}")
        return False

def test_chat_safe():
    """Test chat with safe prompt"""
    print("\n3. Testing Safe Prompt...")
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "prompt": "What is 2 plus 2?",
        "model": "mistral",
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{API_URL}/chat", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('flag') == 'safe':
                print(f"   ✅ Safe prompt processed successfully")
                print(f"   Provider: {result.get('provider', 'unknown')}")
                print(f"   Model: {result.get('model', 'unknown')}")
                print(f"   Response: {result.get('response', '')[:100]}...")
                return True
            else:
                print(f"   ⚠️  Prompt flagged as: {result.get('flag')}")
                return False
        elif response.status_code == 401:
            print(f"   ❌ Authentication failed - check API key")
            return False
        else:
            print(f"   ❌ Chat request failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"   ❌ Chat request error: {e}")
        return False

def test_chat_pii():
    """Test chat with PII detection"""
    print("\n4. Testing PII Detection...")
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "prompt": "My email is john@example.com and my phone is 555-1234",
        "model": "mistral"
    }
    
    try:
        response = requests.post(f"{API_URL}/chat", headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('flag') == 'blocked':
                print(f"   ✅ PII detected and blocked")
                print(f"   Reason: {result.get('reason', 'unknown')}")
                return True
            else:
                print(f"   ⚠️  PII not detected - check PII guard plugin")
                return False
        else:
            print(f"   ❌ Request failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ PII test error: {e}")
        return False

def test_chat_injection():
    """Test SQL injection detection"""
    print("\n5. Testing SQL Injection Detection...")
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "prompt": "SELECT * FROM users WHERE 1=1; DROP TABLE users;",
        "model": "mistral"
    }
    
    try:
        response = requests.post(f"{API_URL}/chat", headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('flag') == 'blocked':
                print(f"   ✅ SQL injection detected and blocked")
                print(f"   Reason: {result.get('reason', 'unknown')}")
                return True
            else:
                print(f"   ⚠️  SQL injection not detected - check basic guard plugin")
                return False
        else:
            print(f"   ❌ Request failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Injection test error: {e}")
        return False

def test_invalid_api_key():
    """Test invalid API key rejection"""
    print("\n6. Testing Invalid API Key...")
    headers = {
        "X-API-Key": "invalid-key-12345",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": "Test prompt",
        "model": "mistral"
    }
    
    try:
        response = requests.post(f"{API_URL}/chat", headers=headers, json=data, timeout=10)
        if response.status_code == 401:
            print(f"   ✅ Invalid API key properly rejected")
            return True
        else:
            print(f"   ❌ Invalid key not rejected: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API key test error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("WAG-TAIL AI GATEWAY OSS EDITION - TEST SUITE")
    print("=" * 60)
    print(f"Testing server at: {API_URL}")
    print(f"Using API key: {API_KEY}")
    
    # Check if server is running
    print("\nChecking if server is running...")
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
    except:
        print("❌ Server is not running. Please start it with:")
        print("   uvicorn main:app --reload")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Plugins", test_plugins()))
    results.append(("Safe Prompt", test_chat_safe()))
    results.append(("PII Detection", test_chat_pii()))
    results.append(("SQL Injection", test_chat_injection()))
    results.append(("Invalid API Key", test_invalid_api_key()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The OSS edition is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())