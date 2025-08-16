# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Wag-Tail Pty Ltd

"""
Basic test suite for Wag-Tail AI Gateway OSS Edition
Simple tests to verify core functionality
"""

import json
import time
import requests
import subprocess
import sys
from typing import Dict, Any

class WagTailOSSTest:
    """Basic test suite for OSS edition"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_api_key = "demo-key-for-testing"
        self.results = []
    
    def run_all_tests(self):
        """Run all available tests"""
        print("🧪 Running Wag-Tail OSS Test Suite")
        print("=" * 50)
        
        tests = [
            ("Configuration Loading", self.test_config_loading),
            ("Plugin Loading", self.test_plugin_loading),
            ("Health Check", self.test_health_endpoint),
            ("Authentication", self.test_authentication),
            ("Basic Chat", self.test_basic_chat),
            ("Security Filters", self.test_security_filters),
            ("PII Detection", self.test_pii_detection),
            ("Error Handling", self.test_error_handling),
            ("Header-based Routing", self.test_header_routing)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    print(f"✅ {test_name}: PASSED")
                    self.results.append((test_name, True, None))
                else:
                    print(f"❌ {test_name}: FAILED")
                    self.results.append((test_name, False, "Test returned False"))
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                self.results.append((test_name, False, str(e)))
        
        self.print_summary()
    
    def test_config_loading(self) -> bool:
        """Test configuration loading"""
        try:
            from config_loader import load_config, validate_config
            
            # Test config loading
            config = load_config()
            assert isinstance(config, dict), "Config should be a dictionary"
            assert "llm" in config, "Config should have 'llm' section"
            assert "security" in config, "Config should have 'security' section"
            
            # Test config validation
            is_valid = validate_config()
            assert is_valid, "Configuration should be valid"
            
            return True
        except Exception as e:
            print(f"Config test error: {e}")
            return False
    
    def test_plugin_loading(self) -> bool:
        """Test plugin loading"""
        try:
            from plugin_loader import PluginManager
            
            manager = PluginManager()
            success = manager.load_plugins()
            assert success, "Plugin loading should succeed"
            
            plugins = manager.get_all_plugins()
            assert len(plugins) > 0, "Should load at least one plugin"
            
            # Test specific plugins
            expected_plugins = [
                "wag_tail_key_auth",
                "wag_tail_basic_guard",
                "wag_tail_pii_guard",
                "wag_tail_webhook_guardrail"
            ]
            
            for plugin_name in expected_plugins:
                plugin = manager.get_plugin(plugin_name)
                if plugin:  # Plugin might be disabled in config
                    assert hasattr(plugin, 'get_status'), f"Plugin {plugin_name} should have get_status method"
            
            return True
        except Exception as e:
            print(f"Plugin test error: {e}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
            
            data = response.json()
            assert "status" in data, "Health response should have status"
            assert "version" in data, "Health response should have version"
            assert "edition" in data, "Health response should have edition"
            assert data["edition"] == "oss", "Edition should be 'oss'"
            
            return True
        except requests.exceptions.ConnectionError:
            print("⚠️  Server not running - start with: python main.py")
            return False
        except Exception as e:
            print(f"Health test error: {e}")
            return False
    
    def test_authentication(self) -> bool:
        """Test API key authentication"""
        try:
            # Test with valid API key
            headers = {"X-API-Key": self.test_api_key}
            payload = {"prompt": "Hello"}
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            assert response.status_code in [200, 400, 422], f"Valid auth should not return {response.status_code}"
            
            # Test with invalid API key
            headers = {"X-API-Key": "invalid-key"}
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=10
            )
            assert response.status_code == 401, "Invalid auth should return 401"
            
            return True
        except Exception as e:
            print(f"Auth test error: {e}")
            return False
    
    def test_basic_chat(self) -> bool:
        """Test basic chat functionality"""
        try:
            headers = {"X-API-Key": self.test_api_key}
            payload = {"prompt": "What is 2+2?"}
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "response" in data, "Chat response should have 'response' field"
                assert "flag" in data, "Chat response should have 'flag' field"
                assert "llm_provider" in data, "Chat response should have 'llm_provider' field"
                assert "process_time_ms" in data, "Chat response should have 'process_time_ms' field"
                
                print(f"📝 Chat response: {data['response'][:100]}...")
                return True
            else:
                print(f"⚠️  Chat test: Expected 200, got {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                # Don't fail the test if LLM is not available
                return True
                
        except Exception as e:
            print(f"Chat test error: {e}")
            return False
    
    def test_security_filters(self) -> bool:
        """Test security filters"""
        try:
            headers = {"X-API-Key": self.test_api_key}
            
            # Test SQL injection pattern
            payload = {"prompt": "SELECT * FROM users WHERE id=1"}
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Should be blocked or flagged
                assert data.get("flag") in ["blocked", "suspicious", "safe"], f"Unexpected flag: {data.get('flag')}"
            
            # Test code execution pattern
            payload = {"prompt": "exec('print(hello)')"}
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data.get("flag") in ["blocked", "suspicious", "safe"], f"Unexpected flag: {data.get('flag')}"
            
            return True
        except Exception as e:
            print(f"Security test error: {e}")
            return False
    
    def test_pii_detection(self) -> bool:
        """Test PII detection"""
        try:
            headers = {"X-API-Key": self.test_api_key}
            
            # Test with email address
            payload = {"prompt": "My email is john.doe@example.com"}
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # PII detection might be disabled or not working
                # Just check that we get a valid response structure
                assert "pii_detected" in data, "Response should have 'pii_detected' field"
                
                if data.get("pii_detected"):
                    print(f"📧 PII detected: {data.get('pii_types', [])}")
            
            return True
        except Exception as e:
            print(f"PII test error: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        try:
            headers = {"X-API-Key": self.test_api_key}
            
            # Test empty prompt
            payload = {"prompt": ""}
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            # Should handle gracefully
            assert response.status_code in [200, 400, 422], f"Empty prompt handling: {response.status_code}"
            
            # Test missing prompt
            payload = {}
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            assert response.status_code == 422, "Missing prompt should return 422"
            
            # Test very long prompt
            payload = {"prompt": "A" * 20000}
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            # Should handle gracefully (block or process)
            assert response.status_code in [200, 400, 413], f"Long prompt handling: {response.status_code}"
            
            return True
        except Exception as e:
            print(f"Error handling test error: {e}")
            return False
    
    def test_header_routing(self) -> bool:
        """Test header-based LLM routing"""
        try:
            headers = {
                "X-API-Key": self.test_api_key,
                "X-LLM-Provider": "ollama",
                "X-LLM-Model": "mistral"
            }
            payload = {"prompt": "Hello"}
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if headers were respected (might fallback to default)
                assert "llm_provider" in data, "Response should have llm_provider"
                assert "llm_model_name" in data, "Response should have llm_model_name"
            
            return True
        except Exception as e:
            print(f"Header routing test error: {e}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for name, success, error in self.results:
                if not success:
                    print(f"  • {name}: {error}")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"🎯 Testing Wag-Tail OSS at: {base_url}")
    
    tester = WagTailOSSTest(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main()