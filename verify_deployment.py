#!/usr/bin/env python3
"""
Deployment Verification Script for JAK Company RAG API v2.4
Tests all endpoints to ensure proper deployment on Render
"""

import requests
import json
import sys
import time
from typing import Dict, Any

def test_endpoint(base_url: str, endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> bool:
    """Test a single endpoint and return success status"""
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    try:
        print(f"Testing {method} {url}...")
        
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"✅ {endpoint} - Status: {response.status_code}")
                return True
            except json.JSONDecodeError:
                print(f"❌ {endpoint} - Invalid JSON response")
                return False
        else:
            print(f"❌ {endpoint} - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint} - Request failed: {str(e)}")
        return False

def main():
    """Main verification function"""
    if len(sys.argv) != 2:
        print("Usage: python verify_deployment.py <base_url>")
        print("Example: python verify_deployment.py https://your-app.onrender.com")
        sys.exit(1)
    
    base_url = sys.argv[1]
    print(f"🚀 Verifying deployment at: {base_url}")
    print("=" * 60)
    
    # Test cases
    tests = [
        {
            "name": "Root Endpoint",
            "endpoint": "/",
            "method": "GET"
        },
        {
            "name": "Health Check",
            "endpoint": "/health",
            "method": "GET"
        },
        {
            "name": "Performance Metrics",
            "endpoint": "/performance_metrics",
            "method": "GET"
        },
        {
            "name": "Memory Status",
            "endpoint": "/memory_status",
            "method": "GET"
        },
        {
            "name": "Main RAG API - Definition Test",
            "endpoint": "/optimize_rag",
            "method": "POST",
            "data": {
                "message": "C'est quoi un ambassadeur ?",
                "session_id": "verification_test"
            }
        },
        {
            "name": "Main RAG API - Payment Test",
            "endpoint": "/optimize_rag",
            "method": "POST",
            "data": {
                "message": "Je n'ai pas été payé pour ma formation",
                "session_id": "verification_test"
            }
        },
        {
            "name": "Clear Memory Test",
            "endpoint": "/clear_memory/verification_test",
            "method": "POST"
        }
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        print(f"\n📋 {test['name']}")
        success = test_endpoint(
            base_url, 
            test['endpoint'], 
            test['method'], 
            test.get('data')
        )
        if success:
            passed_tests += 1
        
        # Small delay between tests
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"📊 VERIFICATION RESULTS")
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Your deployment is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()