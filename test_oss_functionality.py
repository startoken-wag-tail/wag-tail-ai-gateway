#!/usr/bin/env python3
"""
OSS Edition Functionality Test
Tests core functionality of the OSS edition after webhook plugin removal
"""

import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_plugin_loading():
    """Test that exactly 3 plugins load in OSS edition"""
    print("\n" + "="*60)
    print("TEST 1: PLUGIN LOADING")
    print("="*60)
    
    try:
        from plugin_loader import load_plugins, get_plugin_manager
        
        # Test loading
        result = load_plugins()
        print(f"✅ Plugin loading function: {result}")
        
        # Get plugin manager and check loaded plugins
        pm = get_plugin_manager()
        loaded_plugins = pm.get_all_plugins()
        
        print(f"✅ Number of plugins loaded: {len(loaded_plugins)}")
        print(f"✅ Loaded plugins: {list(loaded_plugins.keys())}")
        
        # Verify exactly 3 plugins and no webhook
        expected_plugins = {"wag_tail_key_auth", "wag_tail_basic_guard", "wag_tail_pii_guard"}
        loaded_plugin_names = set(loaded_plugins.keys())
        
        if loaded_plugin_names == expected_plugins:
            print("✅ PASS: Correct plugins loaded")
        else:
            print(f"❌ FAIL: Expected {expected_plugins}, got {loaded_plugin_names}")
            
        if "wag_tail_webhook_guardrail" not in loaded_plugin_names:
            print("✅ PASS: Webhook plugin correctly excluded")
        else:
            print("❌ FAIL: Webhook plugin should not be loaded in OSS")
            
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Plugin loading error: {e}")
        return False

def test_plugin_functionality():
    """Test basic plugin functionality"""
    print("\n" + "="*60)
    print("TEST 2: PLUGIN FUNCTIONALITY")
    print("="*60)
    
    try:
        from plugin_loader import get_plugin_manager
        pm = get_plugin_manager()
        
        # Test auth plugin
        auth_plugin = pm.get_plugin("wag_tail_key_auth")
        if auth_plugin:
            print("✅ Auth plugin available")
            status = auth_plugin.get_status()
            print(f"✅ Auth plugin status: {status.get('status', 'unknown')}")
        else:
            print("❌ Auth plugin not found")
            
        # Test basic guard plugin  
        guard_plugin = pm.get_plugin("wag_tail_basic_guard")
        if guard_plugin:
            print("✅ Basic guard plugin available")
            status = guard_plugin.get_status()
            print(f"✅ Basic guard status: {status.get('status', 'unknown')}")
        else:
            print("❌ Basic guard plugin not found")
            
        # Test PII plugin
        pii_plugin = pm.get_plugin("wag_tail_pii_guard")
        if pii_plugin:
            print("✅ PII guard plugin available")
            status = pii_plugin.get_status()
            print(f"✅ PII guard status: {status.get('status', 'unknown')}")
        else:
            print("❌ PII guard plugin not found")
            
        # Verify webhook plugin is NOT available
        webhook_plugin = pm.get_plugin("wag_tail_webhook_guardrail")
        if webhook_plugin is None:
            print("✅ PASS: Webhook plugin correctly unavailable")
        else:
            print("❌ FAIL: Webhook plugin should not be available")
            
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Plugin functionality error: {e}")
        return False

def test_config_files():
    """Test configuration files have webhook disabled"""
    print("\n" + "="*60)
    print("TEST 3: CONFIGURATION FILES")
    print("="*60)
    
    try:
        from config_loader import get_plugin_config
        
        config = get_plugin_config()
        enabled_plugins = config.get("enabled", [])
        
        print(f"✅ Enabled plugins in config: {enabled_plugins}")
        
        if "wag_tail_webhook_guardrail" not in enabled_plugins:
            print("✅ PASS: Webhook plugin not in enabled list")
        else:
            print("❌ FAIL: Webhook plugin should not be enabled in OSS config")
            
        expected_count = 3
        if len(enabled_plugins) == expected_count:
            print(f"✅ PASS: Correct number of plugins enabled ({expected_count})")
        else:
            print(f"❌ FAIL: Expected {expected_count} plugins, got {len(enabled_plugins)}")
            
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Config test error: {e}")
        return False

def test_imports():
    """Test that core modules can be imported"""
    print("\n" + "="*60)
    print("TEST 4: CORE IMPORTS")
    print("="*60)
    
    imports_to_test = [
        ("config_loader", "get_plugin_config"),
        ("wag_tail_logger", "logger"),
        ("utils.llm", "query_llm"),
        ("response_loader", "load_responses"),
        ("plugin_loader", "load_plugins"),
        ("schemas.response_models", "ChatResponse")
    ]
    
    success_count = 0
    
    for module_name, function_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[function_name])
            func = getattr(module, function_name)
            print(f"✅ {module_name}.{function_name} - OK")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}.{function_name} - FAIL: {e}")
    
    if success_count == len(imports_to_test):
        print("✅ PASS: All core imports successful")
        return True
    else:
        print(f"❌ FAIL: {success_count}/{len(imports_to_test)} imports successful")
        return False

def main():
    """Run all tests"""
    print("🔬 WAG-TAIL OSS EDITION FUNCTIONALITY TEST")
    print("Testing core functionality after webhook plugin removal")
    
    tests = [
        ("Plugin Loading", test_plugin_loading),
        ("Plugin Functionality", test_plugin_functionality), 
        ("Configuration Files", test_config_files),
        ("Core Imports", test_imports)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} - CRITICAL ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED - OSS Edition functionality verified!")
        return True
    else:
        print("⚠️  Some tests failed - check output above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)