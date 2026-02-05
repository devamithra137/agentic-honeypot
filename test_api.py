#!/usr/bin/env python3
"""
Test script for Agentic Honey-Pot API
Tests various scam scenarios and validates responses
"""

import os
import sys
import requests
import json
from typing import Dict

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:10000/api/agentic-honeypot")
API_KEY = os.getenv("API_KEY", "test_api_key")
HEALTH_URL = os.getenv("HEALTH_URL", "http://localhost:10000/health")

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(HEALTH_URL)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_authentication():
    """Test authentication"""
    print("\n🔐 Testing authentication...")
    
    # Test without auth
    try:
        response = requests.post(
            API_URL,
            json={"conversation_id": "test", "message": "test", "history": []},
            timeout=10
        )
        if response.status_code == 401:
            print("✅ Correctly rejected request without auth")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Auth test error: {e}")
    
    # Test with invalid auth
    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": "Bearer invalid_key"},
            json={"conversation_id": "test", "message": "test", "history": []},
            timeout=10
        )
        if response.status_code == 401:
            print("✅ Correctly rejected invalid API key")
            return True
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid auth test error: {e}")
        return False

def validate_response_schema(response_data: Dict) -> bool:
    """Validate response has correct schema"""
    required_keys = {
        "scam_detected", "agent_activated", "agent_reply",
        "engagement_metrics", "extracted_intelligence", "status"
    }
    
    if not all(key in response_data for key in required_keys):
        print("❌ Missing required keys in response")
        return False
    
    # Check engagement_metrics
    metrics = response_data.get("engagement_metrics", {})
    if "turn_count" not in metrics or "engagement_duration" not in metrics:
        print("❌ Invalid engagement_metrics structure")
        return False
    
    # Check extracted_intelligence
    intel = response_data.get("extracted_intelligence", {})
    if not all(key in intel for key in ["bank_accounts", "upi_ids", "phishing_urls"]):
        print("❌ Invalid extracted_intelligence structure")
        return False
    
    # Ensure arrays are never null
    for key in ["bank_accounts", "upi_ids", "phishing_urls"]:
        if intel[key] is None:
            print(f"❌ {key} is null (should be empty array)")
            return False
    
    return True

def test_scam_detection():
    """Test various scam scenarios"""
    print("\n🎯 Testing scam detection...")
    
    test_cases = [
        {
            "name": "Account blocked scam",
            "data": {
                "conversation_id": "test_001",
                "message": "Your account has been blocked. Send OTP to verify: 1234567890",
                "history": []
            },
            "expect_scam": True,
            "expect_intelligence": True
        },
        {
            "name": "UPI payment scam",
            "data": {
                "conversation_id": "test_002",
                "message": "Pay immediately to scammer@paytm or account will be suspended",
                "history": []
            },
            "expect_scam": True,
            "expect_intelligence": True
        },
        {
            "name": "Phishing URL scam",
                "data": {
                "conversation_id": "test_003",
                "message": "Click here to verify KYC: http://fake-bank-verify.com",
                "history": []
            },
            "expect_scam": True,
            "expect_intelligence": True
        },
        {
            "name": "Normal conversation",
            "data": {
                "conversation_id": "test_004",
                "message": "Hello, how are you doing today?",
                "history": []
            },
            "expect_scam": False,
            "expect_intelligence": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=test_case["data"],
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}: {response.text}")
                failed += 1
                continue
            
            data = response.json()
            
            # Validate schema
            if not validate_response_schema(data):
                print(f"  ❌ Invalid response schema")
                failed += 1
                continue
            
            # Check scam detection
            if data["scam_detected"] != test_case["expect_scam"]:
                print(f"  ❌ Scam detection mismatch. Expected: {test_case['expect_scam']}, Got: {data['scam_detected']}")
                failed += 1
                continue
            
            # Check if agent was activated when scam detected
            if test_case["expect_scam"] and not data["agent_activated"]:
                print(f"  ⚠️ Agent not activated for detected scam")
            
            # Check intelligence extraction
            intel = data["extracted_intelligence"]
            has_intelligence = any([
                len(intel["bank_accounts"]) > 0,
                len(intel["upi_ids"]) > 0,
                len(intel["phishing_urls"]) > 0
            ])
            
            if test_case["expect_intelligence"] and not has_intelligence:
                print(f"  ⚠️ Expected intelligence extraction but found none")
            
            print(f"  ✅ Test passed")
            print(f"     Scam detected: {data['scam_detected']}")
            print(f"     Agent reply: {data['agent_reply'][:50]}...")
            print(f"     Intelligence: {intel}")
            
            passed += 1
            
        except Exception as e:
            print(f"  ❌ Test error: {e}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0

def test_multi_turn():
    """Test multi-turn conversation"""
    print("\n🔄 Testing multi-turn conversation...")
    
    conversation_id = "test_multiturn"
    
    turns = [
        "Your account is blocked",
        "What should I do?",
        "Send payment to 1234567890",
    ]
    
    for i, message in enumerate(turns, 1):
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "conversation_id": conversation_id,
                    "message": message,
                    "history": []
                },
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"  ❌ Turn {i} failed: HTTP {response.status_code}")
                return False
            
            data = response.json()
            
            if not validate_response_schema(data):
                print(f"  ❌ Turn {i}: Invalid schema")
                return False
            
            print(f"  ✅ Turn {i}: turn_count={data['engagement_metrics']['turn_count']}, duration={data['engagement_metrics']['engagement_duration']}")
            
        except Exception as e:
            print(f"  ❌ Turn {i} error: {e}")
            return False
    
    return True

def test_malformed_input():
    """Test API handles malformed input gracefully"""
    print("\n🛡️ Testing malformed input handling...")
    
    malformed_cases = [
        {"conversation_id": "test", "message": ""},  # Empty message
        {"conversation_id": "", "message": "test"},  # Empty conversation_id
        {"message": "test"},  # Missing conversation_id
        {"conversation_id": "test"},  # Missing message
        {},  # Empty object
    ]
    
    for i, bad_input in enumerate(malformed_cases, 1):
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=bad_input,
                timeout=10
            )
            
            # Should either reject (422) or handle gracefully (200)
            if response.status_code in [200, 422]:
                print(f"  ✅ Case {i}: Handled gracefully (HTTP {response.status_code})")
            else:
                print(f"  ❌ Case {i}: Unexpected status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Case {i} error: {e}")
            return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Agentic Honey-Pot API Test Suite")
    print("=" * 60)
    
    results = {
        "Health Check": test_health(),
        "Authentication": test_authentication(),
        "Scam Detection": test_scam_detection(),
        "Multi-turn": test_multi_turn(),
        "Malformed Input": test_malformed_input(),
    }
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
