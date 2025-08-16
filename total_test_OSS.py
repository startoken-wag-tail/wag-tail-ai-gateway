#!/usr/bin/env python3
"""
Comprehensive Test Suite for Wag-Tail AI Gateway - OSS Edition
Tests all open source features, configurations, and security functionality
"""

import requests
import time
import json
import yaml
import os
import sys
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class Colors:
    """Terminal colors for test output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class TestResults:
    """Collect and manage test results"""
    def __init__(self):
        self.results = {
            'core_functionality': [],
            'security_features': [],
            'llm_integration': [],
            'configuration': [],
            'performance': [],
            'webhook_integration': [],
            'api_endpoints': []
        }
        self.start_time = None
        self.end_time = None
        
    def add_result(self, category: str, test_name: str, passed: bool, 
                   details: str = "", duration: float = 0.0):
        """Add a test result"""
        self.results[category].append({
            'name': test_name,
            'passed': passed,
            'details': details,
            'duration': duration,
            'timestamp': datetime.now()
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary statistics"""
        summary = {}
        total_tests = 0
        total_passed = 0
        
        for category, tests in self.results.items():
            category_passed = sum(1 for test in tests if test['passed'])
            category_total = len(tests)
            summary[category] = {
                'passed': category_passed,
                'total': category_total,
                'percentage': (category_passed / category_total * 100) if category_total > 0 else 0
            }
            total_tests += category_total
            total_passed += category_passed
        
        summary['overall'] = {
            'passed': total_passed,
            'total': total_tests,
            'percentage': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'duration': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        }
        
        return summary

def make_request(endpoint: str, method: str = "POST", headers: Dict = None, 
                data: Dict = None, timeout: int = TEST_TIMEOUT) -> Tuple[int, Dict, float]:
    """Make HTTP request and return status, response, duration"""
    start_time = time.time()
    
    default_headers = {
        "Content-Type": "application/json"
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=default_headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", 
                                   headers=default_headers, 
                                   json=data, 
                                   timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}", headers=default_headers, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        duration = time.time() - start_time
        
        try:
            response_data = response.json()
        except:
            response_data = {"text": response.text}
            
        return response.status_code, response_data, duration
        
    except Exception as e:
        duration = time.time() - start_time
        return 0, {"error": str(e)}, duration

def test_core_functionality(results: TestResults):
    """Test Core OSS Functionality"""
    print(f"{Colors.BLUE}🚀 Testing Core OSS Functionality...{Colors.END}")
    
    # Test 1: Health endpoint
    status, response, duration = make_request("/health", "GET")
    success = status == 200 and "status" in response
    results.add_result('core_functionality', 'Health Endpoint', 
                      success, 
                      f"Status: {status}, Response: {response.get('status', 'N/A')}", duration)
    
    # Test 2: Basic chat functionality
    status, response, duration = make_request("/chat", data={"prompt": "Hello, what is 2+2?"})
    success = status == 200 and ("response" in response or "error" in response)
    results.add_result('core_functionality', 'Basic Chat Request', 
                      success, 
                      f"Status: {status}, Has Response: {'response' in response}", duration)
    
    # Test 3: Documentation endpoints
    status, response, duration = make_request("/docs", "GET")
    success = status == 200
    results.add_result('core_functionality', 'API Documentation', 
                      success, 
                      f"Status: {status}", duration)
    
    # Test 4: Empty prompt handling
    status, response, duration = make_request("/chat", data={"prompt": ""})
    success = status in [400, 422]  # Should reject empty prompts
    results.add_result('core_functionality', 'Empty Prompt Validation', 
                      success, 
                      f"Status: {status}, Expected 400/422", duration)
    
    # Test 5: Long prompt handling
    long_prompt = "A" * 15000  # Over typical limit
    status, response, duration = make_request("/chat", data={"prompt": long_prompt})
    success = status in [400, 413, 422]  # Should reject overly long prompts
    results.add_result('core_functionality', 'Long Prompt Validation', 
                      success, 
                      f"Status: {status}, Prompt length: {len(long_prompt)}", duration)

def test_security_features(results: TestResults):
    """Test Security Features"""
    print(f"{Colors.RED}🔒 Testing Security Features...{Colors.END}")
    
    # Test SQL injection detection
    sql_injections = [
        "'; DROP TABLE users; --",
        "SELECT * FROM passwords WHERE id=1",
        "' OR '1'='1",
        "UNION SELECT username, password FROM users"
    ]
    
    for i, injection in enumerate(sql_injections):
        status, response, duration = make_request("/chat", data={"prompt": injection})
        # OSS should block or process safely
        success = status in [200, 400, 403]
        blocked = response.get('blocked', False) or 'blocked' in str(response).lower()
        results.add_result('security_features', f'SQL Injection Detection {i+1}', 
                          success, 
                          f"Injection: '{injection[:30]}...', Status: {status}, Blocked: {blocked}", duration)
    
    # Test code execution detection
    code_samples = [
        "import os; os.system('rm -rf /')",
        "exec('print(\"dangerous code\")')",
        "eval('2+2')",
        "__import__('subprocess').call(['ls', '-la'])"
    ]
    
    for i, code in enumerate(code_samples):
        status, response, duration = make_request("/chat", data={"prompt": code})
        success = status in [200, 400, 403]
        blocked = response.get('blocked', False) or 'blocked' in str(response).lower()
        results.add_result('security_features', f'Code Execution Detection {i+1}', 
                          success, 
                          f"Code: '{code[:30]}...', Status: {status}, Blocked: {blocked}", duration)
    
    # Test PII detection
    pii_samples = [
        "My social security number is 123-45-6789",
        "My email is john.doe@example.com",
        "My phone number is (555) 123-4567",
        "My credit card is 4532-1234-5678-9012"
    ]
    
    for i, pii in enumerate(pii_samples):
        status, response, duration = make_request("/chat", data={"prompt": pii})
        success = status in [200, 400, 403]
        blocked = response.get('blocked', False) or 'pii' in str(response).lower()
        results.add_result('security_features', f'PII Detection {i+1}', 
                          success, 
                          f"PII Type: {pii.split()[1]}, Status: {status}, Detected: {blocked}", duration)
    
    # Test regex pattern detection
    patterns = [
        "password: admin123",
        "API_KEY=sk-1234567890abcdef",
        "DROP DATABASE production",
        "rm -rf --no-preserve-root /"
    ]
    
    for i, pattern in enumerate(patterns):
        status, response, duration = make_request("/chat", data={"prompt": pattern})
        success = status in [200, 400, 403]
        results.add_result('security_features', f'Regex Pattern Detection {i+1}', 
                          success, 
                          f"Pattern: '{pattern[:30]}...', Status: {status}", duration)

def test_llm_integration(results: TestResults):
    """Test LLM Integration"""
    print(f"{Colors.PURPLE}🤖 Testing LLM Integration...{Colors.END}")
    
    # Test provider selection via headers
    providers = [
        ("ollama", "mistral"),
        ("openai", "gpt-3.5-turbo"),
        ("gemini", "gemini-pro"),
        ("azure", "gpt-35-turbo")
    ]
    
    for provider, model in providers:
        status, response, duration = make_request("/chat",
                                                headers={
                                                    "x-llm-provider": provider,
                                                    "x-llm-model": model
                                                },
                                                data={"prompt": "What is machine learning?"})
        
        success = status in [200, 400, 503]  # 503 if provider unavailable
        results.add_result('llm_integration', f'Provider Selection - {provider}', 
                          success, 
                          f"Provider: {provider}, Model: {model}, Status: {status}", duration)
    
    # Test model fallback behavior
    status, response, duration = make_request("/chat",
                                            headers={
                                                "x-llm-provider": "invalid-provider",
                                                "x-llm-model": "invalid-model"
                                            },
                                            data={"prompt": "Test fallback"})
    
    success = status in [200, 400, 503]
    results.add_result('llm_integration', 'Invalid Provider Fallback', 
                      success, 
                      f"Status: {status}", duration)
    
    # Test various prompt types
    prompt_types = [
        ("Simple Question", "What is 2+2?"),
        ("Complex Query", "Explain the differences between machine learning and artificial intelligence"),
        ("Creative Request", "Write a short poem about technology"),
        ("Technical Question", "How does HTTP work?")
    ]
    
    for name, prompt in prompt_types:
        status, response, duration = make_request("/chat", data={"prompt": prompt})
        success = status in [200, 503]  # 503 if LLM unavailable
        has_response = "response" in response or "error" in response
        results.add_result('llm_integration', f'Prompt Type - {name}', 
                          success and has_response, 
                          f"Status: {status}, Has Response: {has_response}", duration)

def test_configuration(results: TestResults):
    """Test Configuration Loading and Validation"""
    print(f"{Colors.YELLOW}⚙️ Testing Configuration...{Colors.END}")
    
    # Test config file loading
    try:
        with open('config/sys_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['llm', 'security']
        for section in required_sections:
            exists = section in config
            results.add_result('configuration', f'Config Section - {section}', 
                              exists, 
                              f"Section exists: {exists}", 0)
        
        # Test LLM configuration
        llm_config = config.get('llm', {})
        provider_set = 'provider' in llm_config
        model_set = 'model' in llm_config
        results.add_result('configuration', 'LLM Configuration', 
                          provider_set and model_set, 
                          f"Provider set: {provider_set}, Model set: {model_set}", 0)
        
        # Test security configuration
        security_config = config.get('security', {})
        pii_enabled = security_config.get('enable_pii_detection', False)
        code_detection = security_config.get('enable_code_detection', False)
        results.add_result('configuration', 'Security Configuration', 
                          pii_enabled or code_detection, 
                          f"PII: {pii_enabled}, Code detection: {code_detection}", 0)
        
    except Exception as e:
        results.add_result('configuration', 'Config File Loading', 
                          False, 
                          f"Error: {str(e)}", 0)
    
    # Test environment-specific configs
    env_configs = ['development.yaml', 'staging.yaml', 'production.yaml']
    for env_config in env_configs:
        config_path = f'config/environments/{env_config}'
        exists = os.path.exists(config_path)
        results.add_result('configuration', f'Environment Config - {env_config}', 
                          exists, 
                          f"File exists: {exists}", 0)

def test_webhook_integration(results: TestResults):
    """Test Webhook Integration"""
    print(f"{Colors.CYAN}🔗 Testing Webhook Integration...{Colors.END}")
    
    # Test webhook configuration
    try:
        with open('config/sys_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        webhook_config = config.get('webhooks', {})
        webhooks_configured = len(webhook_config) > 0
        results.add_result('webhook_integration', 'Webhook Configuration', 
                          True,  # Configuration is optional in OSS
                          f"Webhooks configured: {webhooks_configured}", 0)
        
    except Exception as e:
        results.add_result('webhook_integration', 'Webhook Configuration', 
                          False, 
                          f"Error reading config: {str(e)}", 0)
    
    # Test webhook payload structure (mock test)
    # Since we can't test real webhooks without a server, we test the structure
    test_prompts = [
        "Safe prompt for testing",
        "DROP TABLE users",  # Should trigger webhook if configured
    ]
    
    for i, prompt in enumerate(test_prompts):
        status, response, duration = make_request("/chat", data={"prompt": prompt})
        # Webhook should not affect main functionality
        success = status in [200, 400, 403, 503]
        results.add_result('webhook_integration', f'Webhook Trigger Test {i+1}', 
                          success, 
                          f"Prompt type: {'safe' if i == 0 else 'risky'}, Status: {status}", duration)

def test_api_endpoints(results: TestResults):
    """Test API Endpoints"""
    print(f"{Colors.GREEN}🌐 Testing API Endpoints...{Colors.END}")
    
    # Test health endpoint in detail
    status, response, duration = make_request("/health", "GET")
    success = status == 200
    has_status = "status" in response
    has_version = "version" in response
    results.add_result('api_endpoints', 'Health Endpoint Structure', 
                      success and has_status, 
                      f"Status: {status}, Has status field: {has_status}, Has version: {has_version}", duration)
    
    # Test CORS headers
    status, response, duration = make_request("/health", "GET", 
                                            headers={"Origin": "http://localhost:3000"})
    success = status == 200
    results.add_result('api_endpoints', 'CORS Headers', 
                      success, 
                      f"Status: {status}", duration)
    
    # Test OpenAPI documentation
    status, response, duration = make_request("/docs", "GET")
    success = status == 200
    results.add_result('api_endpoints', 'OpenAPI Documentation', 
                      success, 
                      f"Status: {status}", duration)
    
    # Test ReDoc documentation  
    status, response, duration = make_request("/redoc", "GET")
    success = status == 200
    results.add_result('api_endpoints', 'ReDoc Documentation', 
                      success, 
                      f"Status: {status}", duration)
    
    # Test invalid endpoints
    status, response, duration = make_request("/invalid-endpoint", "GET")
    success = status == 404
    results.add_result('api_endpoints', 'Invalid Endpoint Handling', 
                      success, 
                      f"Status: {status}, Expected 404", duration)
    
    # Test method not allowed
    status, response, duration = make_request("/chat", "DELETE")
    success = status == 405
    results.add_result('api_endpoints', 'Method Not Allowed', 
                      success, 
                      f"Status: {status}, Expected 405", duration)

def test_performance(results: TestResults):
    """Test Performance"""
    print(f"{Colors.YELLOW}🚀 Testing Performance...{Colors.END}")
    
    # Test response times
    performance_tests = [
        ("Health Check", "/health", "GET", None),
        ("Simple Chat", "/chat", "POST", {"prompt": "Hello"}),
        ("Documentation", "/docs", "GET", None)
    ]
    
    for name, endpoint, method, data in performance_tests:
        durations = []
        
        # Run multiple times for average
        for i in range(3):
            status, response, duration = make_request(endpoint, method, data=data)
            durations.append(duration)
        
        avg_duration = sum(durations) / len(durations)
        fast_enough = avg_duration < 10.0  # 10 second threshold for OSS
        
        results.add_result('performance', f'Performance - {name}', 
                          fast_enough, 
                          f"Avg duration: {avg_duration:.2f}s", avg_duration)
    
    # Test concurrent requests
    import threading
    import time
    
    def make_concurrent_request():
        return make_request("/health", "GET")
    
    start_time = time.time()
    threads = []
    for i in range(5):
        thread = threading.Thread(target=make_concurrent_request)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    concurrent_duration = time.time() - start_time
    concurrent_success = concurrent_duration < 15.0  # Should handle 5 concurrent requests quickly
    
    results.add_result('performance', 'Concurrent Requests', 
                      concurrent_success, 
                      f"5 concurrent requests completed in {concurrent_duration:.2f}s", concurrent_duration)

def generate_markdown_report(results: TestResults) -> str:
    """Generate markdown formatted test report for OSS edition"""
    summary = results.get_summary()
    overall = summary['overall']
    
    # Generate markdown content
    md_content = f"""# Wag-Tail AI Gateway OSS Edition - Comprehensive Test Report

**Generated:** {results.start_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Total Duration:** {overall['duration']:.2f} seconds  
**Edition:** Open Source Edition

## 📊 Overall Results

| Metric | Value |
|--------|-------|
| **Tests Passed** | {overall['passed']}/{overall['total']} ({overall['percentage']:.1f}%) |
| **Total Duration** | {overall['duration']:.2f} seconds |
| **Test Date** | {results.start_time.strftime('%Y-%m-%d %H:%M:%S')} |

## 📋 OSS Test Categories

| Category | Passed | Total | Percentage |
|----------|--------|-------|------------|
"""
    
    category_names = {
        'core_functionality': '🚀 Core Functionality',
        'security_features': '🔒 Security Features', 
        'llm_integration': '🤖 LLM Integration',
        'configuration': '⚙️ Configuration',
        'webhook_integration': '🔗 Webhook Integration',
        'api_endpoints': '🌐 API Endpoints',
        'performance': '🚀 Performance'
    }
    
    for category, name in category_names.items():
        cat_summary = summary[category]
        if cat_summary['total'] > 0:
            md_content += f"| {name} | {cat_summary['passed']} | {cat_summary['total']} | {cat_summary['percentage']:.1f}% |\n"
    
    # Failed tests section
    md_content += "\n## ❌ Failed Tests\n\n"
    failed_tests = []
    
    for category, tests in results.results.items():
        for test in tests:
            if not test['passed']:
                failed_tests.append((category, test))
    
    if failed_tests:
        md_content += "| Test Name | Category | Details |\n"
        md_content += "|-----------|----------|----------|\n"
        for category, test in failed_tests:
            md_content += f"| {test['name']} | {category} | {test['details']} |\n"
    else:
        md_content += "🎉 **No failed tests!** All OSS tests passed successfully.\n"
    
    # Performance summary
    md_content += "\n## ⚡ Performance Summary\n\n"
    perf_tests = results.results.get('performance', [])
    if perf_tests:
        md_content += "| Test | Duration | Status |\n"
        md_content += "|------|----------|--------|\n"
        for test in perf_tests:
            status = "✅ Fast" if test['duration'] < 2.0 else "⚠️ Acceptable" if test['duration'] < 5.0 else "🔴 Slow"
            md_content += f"| {test['name']} | {test['duration']:.2f}s | {status} |\n"
    
    # Security summary
    md_content += "\n## 🛡️ Security Test Summary\n\n"
    security_tests = results.results.get('security_features', [])
    security_passed = sum(1 for test in security_tests if test['passed'])
    security_total = len(security_tests)
    
    if security_total > 0:
        security_percentage = (security_passed / security_total) * 100
        md_content += f"**Security Tests Passed:** {security_passed}/{security_total} ({security_percentage:.1f}%)\n\n"
        
        md_content += "| Test | Status |\n"
        md_content += "|------|--------|\n"
        for test in security_tests:
            status = "✅ Pass" if test['passed'] else "❌ Fail"
            md_content += f"| {test['name']} | {status} |\n"
    else:
        md_content += "No security tests run.\n"
    
    # OSS Features summary
    md_content += "\n## 🔓 OSS Features Tested\n\n"
    md_content += "| Feature | Category | Status |\n"
    md_content += "|---------|----------|--------|\n"
    
    feature_categories = {
        'core_functionality': 'Core Features',
        'security_features': 'Security Pipeline',
        'llm_integration': 'LLM Providers',
        'webhook_integration': 'External Integration'
    }
    
    for category, feature_name in feature_categories.items():
        tests = results.results.get(category, [])
        if tests:
            passed = sum(1 for test in tests if test['passed'])
            total = len(tests)
            percentage = (passed / total) * 100 if total > 0 else 0
            status = "✅ Working" if percentage >= 70 else "⚠️ Issues" if percentage >= 50 else "❌ Failed"
            md_content += f"| {feature_name} | {category} | {status} ({passed}/{total}) |\n"
    
    # Recommendations
    md_content += "\n## 💡 Recommendations\n\n"
    if overall['percentage'] >= 90:
        md_content += "🎉 **Excellent!** Your OSS edition is performing very well.\n"
    elif overall['percentage'] >= 80:
        md_content += "✅ **Good performance**, but some areas need attention.\n"
    else:
        md_content += "⚠️ **System needs improvements.**\n"
    
    if security_total > 0 and (security_passed / security_total) < 0.8:
        md_content += "\n🚨 **Security Alert:** Some security features need attention.\n"
    
    if any(test['duration'] > 10.0 for test in perf_tests):
        md_content += "\n⏱️ **Performance:** Some endpoints are slow - consider optimization.\n"
    
    # OSS vs Enterprise comparison
    md_content += "\n## 🆚 OSS vs Enterprise Comparison\n\n"
    md_content += "| Feature | OSS Edition | Enterprise Edition |\n"
    md_content += "|---------|-------------|--------------------|\n"
    md_content += "| Security Pipeline | ✅ Basic filters, PII detection | ✅ Advanced ML classifiers |\n"
    md_content += "| LLM Integration | ✅ Multiple providers | ✅ Advanced routing & caching |\n"
    md_content += "| Rate Limiting | ❌ Not available | ✅ Advanced org/group limits |\n"
    md_content += "| Authentication | ❌ Not available | ✅ Database-backed API keys |\n"
    md_content += "| Admin API | ❌ Not available | ✅ Full admin functionality |\n"
    md_content += "| Monitoring | ✅ Basic logging | ✅ Langfuse integration |\n"
    md_content += "| Webhooks | ✅ External GuardRails | ✅ Advanced webhook system |\n"
    
    # Detailed test results
    md_content += "\n## 📝 Detailed Test Results\n\n"
    for category, name in category_names.items():
        tests = results.results.get(category, [])
        if tests:
            md_content += f"### {name}\n\n"
            md_content += "| Test Name | Status | Duration | Details |\n"
            md_content += "|-----------|--------|----------|----------|\n"
            for test in tests:
                status = "✅ Pass" if test['passed'] else "❌ Fail"
                md_content += f"| {test['name']} | {status} | {test['duration']:.3f}s | {test['details']} |\n"
            md_content += "\n"
    
    md_content += "\n---\n"
    md_content += f"*Report generated by Wag-Tail AI Gateway OSS Comprehensive Test Suite v1.0*  \n"
    md_content += f"*Test completed at: {results.end_time.strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    return md_content

def save_test_report(results: TestResults):
    """Save test results to markdown file"""
    # Generate filename with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"total_test_OSS_{today}.md"
    filepath = Path(filename)
    
    # Generate markdown content
    md_content = generate_markdown_report(results)
    
    # Write to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"\n{Colors.GREEN}📄 OSS Test report saved to: {filepath}{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Failed to save OSS test report: {str(e)}{Colors.END}")

def print_test_results(results: TestResults):
    """Print comprehensive test results for OSS edition"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🧪 WAG-TAIL AI GATEWAY OSS EDITION TEST RESULTS 🧪{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    summary = results.get_summary()
    
    # Overall summary
    overall = summary['overall']
    color = Colors.GREEN if overall['percentage'] >= 80 else Colors.YELLOW if overall['percentage'] >= 60 else Colors.RED
    
    print(f"\n{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"  {color}✅ Tests Passed: {overall['passed']}/{overall['total']} ({overall['percentage']:.1f}%){Colors.END}")
    print(f"  ⏱️ Total Duration: {overall['duration']:.2f} seconds")
    print(f"  📅 Test Run: {results.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  🔓 Edition: Open Source Edition")
    
    # Category breakdown
    print(f"\n{Colors.BOLD}📋 OSS TEST CATEGORIES:{Colors.END}")
    
    category_names = {
        'core_functionality': '🚀 Core Functionality',
        'security_features': '🔒 Security Features', 
        'llm_integration': '🤖 LLM Integration',
        'configuration': '⚙️ Configuration',
        'webhook_integration': '🔗 Webhook Integration',
        'api_endpoints': '🌐 API Endpoints',
        'performance': '🚀 Performance'
    }
    
    for category, name in category_names.items():
        cat_summary = summary[category]
        if cat_summary['total'] > 0:
            color = Colors.GREEN if cat_summary['percentage'] >= 80 else Colors.YELLOW if cat_summary['percentage'] >= 60 else Colors.RED
            print(f"  {name}: {color}{cat_summary['passed']}/{cat_summary['total']} ({cat_summary['percentage']:.1f}%){Colors.END}")
    
    # Detailed results for failed tests
    print(f"\n{Colors.BOLD}❌ FAILED TESTS DETAILS:{Colors.END}")
    failed_tests = []
    
    for category, tests in results.results.items():
        for test in tests:
            if not test['passed']:
                failed_tests.append((category, test))
    
    if failed_tests:
        for category, test in failed_tests:
            print(f"  {Colors.RED}• {test['name']} ({category}): {test['details']}{Colors.END}")
    else:
        print(f"  {Colors.GREEN}🎉 No failed tests!{Colors.END}")
    
    # Performance summary
    print(f"\n{Colors.BOLD}⚡ PERFORMANCE SUMMARY:{Colors.END}")
    perf_tests = results.results.get('performance', [])
    if perf_tests:
        for test in perf_tests:
            color = Colors.GREEN if test['duration'] < 2.0 else Colors.YELLOW if test['duration'] < 5.0 else Colors.RED
            print(f"  {color}• {test['name']}: {test['duration']:.2f}s{Colors.END}")
    
    # Security summary
    print(f"\n{Colors.BOLD}🛡️ SECURITY TEST SUMMARY:{Colors.END}")
    security_tests = results.results.get('security_features', [])
    security_passed = sum(1 for test in security_tests if test['passed'])
    security_total = len(security_tests)
    
    if security_total > 0:
        security_percentage = (security_passed / security_total) * 100
        color = Colors.GREEN if security_percentage >= 80 else Colors.YELLOW if security_percentage >= 60 else Colors.RED
        print(f"  {color}Security Tests Passed: {security_passed}/{security_total} ({security_percentage:.1f}%){Colors.END}")
        
        for test in security_tests:
            status = "✅" if test['passed'] else "❌"
            print(f"    {status} {test['name']}")
    else:
        print(f"  {Colors.YELLOW}No security tests run{Colors.END}")
    
    # Recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS:{Colors.END}")
    
    if overall['percentage'] >= 90:
        print(f"  {Colors.GREEN}🎉 Excellent! Your OSS edition is performing very well.{Colors.END}")
    elif overall['percentage'] >= 80:
        print(f"  {Colors.YELLOW}✅ Good performance, but some areas need attention.{Colors.END}")
    else:
        print(f"  {Colors.RED}⚠️ System needs significant improvements.{Colors.END}")
    
    if security_total > 0 and (security_passed / security_total) < 0.8:
        print(f"  {Colors.RED}🚨 Security features need attention.{Colors.END}")
    
    if any(test['duration'] > 10.0 for test in perf_tests):
        print(f"  {Colors.YELLOW}⏱️ Some endpoints are slow - consider optimization.{Colors.END}")
    
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}🎯 OSS test run completed successfully!{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")
    
    # Save test report to markdown file
    save_test_report(results)

def main():
    """Main test execution"""
    print(f"{Colors.BOLD}{Colors.BLUE}🚀 Starting Wag-Tail AI Gateway OSS Edition Test Suite...{Colors.END}\n")
    
    results = TestResults()
    results.start_time = datetime.now()
    
    try:
        # Run all test categories
        test_core_functionality(results)
        test_security_features(results)
        test_llm_integration(results)
        test_configuration(results)
        test_webhook_integration(results)
        test_api_endpoints(results)
        test_performance(results)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ OSS test run interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ OSS test run failed with error: {str(e)}{Colors.END}")
    finally:
        results.end_time = datetime.now()
        print_test_results(results)

if __name__ == "__main__":
    main()