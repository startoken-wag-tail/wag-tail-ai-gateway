# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Wag-Tail Pty Ltd

"""
Configuration Loader Test Suite for Wag-Tail AI Gateway OSS Edition
Tests environment detection, configuration merging, validation, and environment variable overrides
"""

import os
import tempfile
import unittest
import yaml
from unittest.mock import patch
from pathlib import Path

# Import the configuration loader
import sys
sys.path.append('..')
from config_loader import ConfigurationLoader, ConfigurationError, load_config, get_environment

class TestOSSConfigurationLoader(unittest.TestCase):
    """Test suite for OSS ConfigurationLoader"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)
        self.env_dir = self.config_dir / "environments"
        self.env_dir.mkdir(exist_ok=True)
        
        # Sample base configuration for OSS
        self.base_config = {
            "edition": "oss",
            "llm": {
                "provider": "ollama",
                "model": "mistral",
                "api_url": "http://localhost:11434/api/generate",
                "timeout": 60
            },
            "security": {
                "enable_pii_detection": True,
                "enable_code_detection": True,
                "max_prompt_length": 10000
            },
            "api": {
                "default_api_key": "test-key"
            },
            "logging": {
                "level": "INFO",
                "format": "json"
            },
            "plugins": {
                "enabled": [
                    "wag_tail_key_auth",
                    "wag_tail_basic_guard",
                    "wag_tail_pii_guard",
                    "wag_tail_webhook_guardrail"
                ]
            }
        }
        
        # Sample development configuration
        self.dev_config = {
            "llm": {
                "timeout": 120
            },
            "security": {
                "max_prompt_length": 15000
            },
            "logging": {
                "level": "DEBUG",
                "format": "text"
            }
        }
        
        # Sample production configuration
        self.prod_config = {
            "llm": {
                "provider": "openai",
                "api_key": "${OPENAI_API_KEY}"
            },
            "security": {
                "max_prompt_length": 8000,
                "pii_confidence_threshold": 0.9
            },
            "api": {
                "default_api_key": "${PRODUCTION_API_KEY}"
            }
        }
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _write_config_file(self, filename: str, config: dict):
        """Helper to write configuration files"""
        filepath = self.config_dir / filename
        with open(filepath, 'w') as f:
            yaml.dump(config, f)
    
    def _write_env_config(self, env: str, config: dict):
        """Helper to write environment configuration files"""
        filepath = self.env_dir / f"{env}.yaml"
        with open(filepath, 'w') as f:
            yaml.dump(config, f)
    
    def test_environment_detection(self):
        """Test environment detection from environment variables"""
        # Test default environment
        loader = ConfigurationLoader(str(self.config_dir))
        self.assertEqual(loader.get_environment(), "development")
        
        # Test explicit environment
        with patch.dict(os.environ, {"WAGTAIL_ENVIRONMENT": "production"}):
            loader = ConfigurationLoader(str(self.config_dir))
            self.assertEqual(loader.get_environment(), "production")
        
        # Test invalid environment
        with patch.dict(os.environ, {"WAGTAIL_ENVIRONMENT": "invalid"}):
            loader = ConfigurationLoader(str(self.config_dir))
            self.assertEqual(loader.get_environment(), "development")
    
    def test_base_config_loading(self):
        """Test loading of base configuration file"""
        self._write_config_file("sys_config.yaml", self.base_config)
        
        loader = ConfigurationLoader(str(self.config_dir))
        config = loader.load_config()
        
        self.assertEqual(config["edition"], "oss")
        self.assertEqual(config["llm"]["provider"], "ollama")
        self.assertEqual(config["security"]["max_prompt_length"], 10000)
    
    def test_environment_config_loading(self):
        """Test loading of environment-specific configuration"""
        self._write_config_file("sys_config.yaml", self.base_config)
        self._write_env_config("development", self.dev_config)
        
        with patch.dict(os.environ, {"WAGTAIL_ENVIRONMENT": "development"}):
            loader = ConfigurationLoader(str(self.config_dir))
            config = loader.load_config()
        
        # Check environment overrides
        self.assertEqual(config["llm"]["timeout"], 120)  # Overridden
        self.assertEqual(config["security"]["max_prompt_length"], 15000)  # Overridden
        self.assertEqual(config["logging"]["level"], "DEBUG")  # Overridden
        self.assertEqual(config["logging"]["format"], "text")  # Overridden
        
        # Check preserved values
        self.assertEqual(config["llm"]["provider"], "ollama")  # Preserved
        self.assertEqual(config["edition"], "oss")  # Preserved
    
    def test_deep_merge(self):
        """Test deep merging of configuration dictionaries"""
        self._write_config_file("sys_config.yaml", self.base_config)
        self._write_env_config("production", self.prod_config)
        
        with patch.dict(os.environ, {"WAGTAIL_ENVIRONMENT": "production"}):
            loader = ConfigurationLoader(str(self.config_dir))
            config = loader.load_config()
        
        # Check deep merge worked correctly
        self.assertEqual(config["llm"]["provider"], "openai")  # Overridden
        self.assertEqual(config["llm"]["model"], "mistral")  # Preserved from base
        self.assertEqual(config["security"]["max_prompt_length"], 8000)  # Overridden
        self.assertTrue(config["security"]["enable_pii_detection"])  # Preserved
    
    def test_environment_variable_overrides(self):
        """Test environment variable overrides"""
        self._write_config_file("sys_config.yaml", self.base_config)
        
        env_vars = {
            "WAGTAIL_LLM_PROVIDER": "openai",
            "WAGTAIL_LLM_MODEL": "gpt-4",
            "OPENAI_API_KEY": "demo-openai-key",
            "WAGTAIL_LOGGING_LEVEL": "WARNING",
            "MAX_PROMPT_LENGTH": "5000",
            "DEFAULT_API_KEY": "custom-api-key"
        }
        
        with patch.dict(os.environ, env_vars):
            loader = ConfigurationLoader(str(self.config_dir))
            config = loader.load_config()
        
        # Check LLM overrides
        self.assertEqual(config["llm"]["provider"], "openai")
        self.assertEqual(config["llm"]["model"], "gpt-4")
        self.assertEqual(config["llm"]["api_key"], "demo-openai-key")
        
        # Check logging override
        self.assertEqual(config["logging"]["level"], "WARNING")
        
        # Check security override
        self.assertEqual(config["security"]["max_prompt_length"], 5000)
        
        # Check API override
        self.assertEqual(config["api"]["default_api_key"], "custom-api-key")
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test valid configuration
        self._write_config_file("sys_config.yaml", self.base_config)
        loader = ConfigurationLoader(str(self.config_dir))
        
        # Should not raise exception
        config = loader.load_config()
        self.assertIsInstance(config, dict)
    
    def test_production_validation(self):
        """Test production-specific validation"""
        # Test production with test API key (should fail)
        prod_config_invalid = self.base_config.copy()
        prod_config_invalid["api"]["default_api_key"] = "demo-key-for-testing"
        
        self._write_config_file("sys_config.yaml", prod_config_invalid)
        
        with patch.dict(os.environ, {"WAGTAIL_ENVIRONMENT": "production"}):
            loader = ConfigurationLoader(str(self.config_dir))
            
            with self.assertRaises(ConfigurationError):
                loader.load_config()
    
    def test_llm_config_validation(self):
        """Test LLM configuration validation"""
        config_with_invalid_llm = self.base_config.copy()
        config_with_invalid_llm["llm"] = {
            "provider": "openai",
            # Missing API key for cloud provider
        }
        
        self._write_config_file("sys_config.yaml", config_with_invalid_llm)
        loader = ConfigurationLoader(str(self.config_dir))
        
        # Should load but log warnings
        config = loader.load_config()
        self.assertIsInstance(config, dict)
    
    def test_missing_config_file(self):
        """Test behavior when configuration file is missing"""
        loader = ConfigurationLoader(str(self.config_dir))
        config = loader.load_config()
        
        # Should return default configuration
        self.assertEqual(config["edition"], "oss")
        self.assertEqual(config["llm"]["provider"], "ollama")
        self.assertIn("plugins", config)
    
    def test_invalid_yaml(self):
        """Test handling of invalid YAML configuration"""
        invalid_yaml = "invalid: yaml: content: [unclosed"
        
        config_file = self.config_dir / "sys_config.yaml"
        with open(config_file, 'w') as f:
            f.write(invalid_yaml)
        
        loader = ConfigurationLoader(str(self.config_dir))
        
        with self.assertRaises(ConfigurationError):
            loader.load_config()
    
    def test_config_caching(self):
        """Test configuration caching in production"""
        self._write_config_file("sys_config.yaml", self.base_config)
        
        with patch.dict(os.environ, {"WAGTAIL_ENVIRONMENT": "production"}):
            loader = ConfigurationLoader(str(self.config_dir))
            
            # First load
            config1 = loader.load_config()
            
            # Modify config file
            modified_config = self.base_config.copy()
            modified_config["llm"]["timeout"] = 120
            self._write_config_file("sys_config.yaml", modified_config)
            
            # Second load (should use cache)
            config2 = loader.load_config()
            self.assertEqual(config2["llm"]["timeout"], 60)  # Original value
            
            # Force reload
            config3 = loader.load_config(force_reload=True)
            self.assertEqual(config3["llm"]["timeout"], 120)  # New value
    
    def test_plugin_functions(self):
        """Test plugin-related configuration functions"""
        self._write_config_file("sys_config.yaml", self.base_config)
        
        loader = ConfigurationLoader(str(self.config_dir))
        config = loader.load_config()
        
        # Test plugin configuration retrieval
        from config_loader import get_plugin_config, is_plugin_enabled
        
        plugin_config = get_plugin_config()
        self.assertIn("enabled", plugin_config)
        
        # Test plugin checking
        self.assertTrue(is_plugin_enabled("wag_tail_key_auth"))
        self.assertFalse(is_plugin_enabled("nonexistent_plugin"))
    
    def test_webhook_configuration(self):
        """Test webhook configuration"""
        config_with_webhook = self.base_config.copy()
        config_with_webhook["webhook"] = {
            "enabled": True,
            "url": "https://example.com/webhook",
            "hmac_secret": "secret"
        }
        
        self._write_config_file("sys_config.yaml", config_with_webhook)
        
        loader = ConfigurationLoader(str(self.config_dir))
        config = loader.load_config()
        
        from config_loader import get_webhook_config
        webhook_config = get_webhook_config()
        
        self.assertTrue(webhook_config["enabled"])
        self.assertEqual(webhook_config["url"], "https://example.com/webhook")
    
    def test_validate_config_function(self):
        """Test standalone config validation function"""
        from config_loader import validate_config
        
        # Test with valid config
        self._write_config_file("sys_config.yaml", self.base_config)
        self.assertTrue(validate_config())
        
        # Test with invalid config (missing provider)
        invalid_config = self.base_config.copy()
        invalid_config["llm"] = {}
        self._write_config_file("sys_config.yaml", invalid_config)
        self.assertFalse(validate_config())

class TestOSSConfigurationFunctions(unittest.TestCase):
    """Test OSS-specific configuration functions"""
    
    @patch('config_loader._config_loader')
    def test_get_default_api_key(self, mock_loader):
        """Test get_default_api_key function"""
        mock_loader.load_config.return_value = {
            "api": {"default_api_key": "test-key"}
        }
        
        from config_loader import get_default_api_key
        api_key = get_default_api_key()
        self.assertEqual(api_key, "test-key")
    
    @patch('config_loader._config_loader')
    def test_get_llm_config(self, mock_loader):
        """Test get_llm_config function"""
        mock_loader.load_config.return_value = {
            "llm": {"provider": "ollama", "model": "mistral"}
        }
        
        from config_loader import get_llm_config
        llm_config = get_llm_config()
        self.assertEqual(llm_config["provider"], "ollama")
        self.assertEqual(llm_config["model"], "mistral")
    
    @patch('config_loader._config_loader')
    def test_get_security_config(self, mock_loader):
        """Test get_security_config function"""
        mock_loader.load_config.return_value = {
            "security": {
                "enable_pii_detection": True,
                "max_prompt_length": 10000
            }
        }
        
        from config_loader import get_security_config
        security_config = get_security_config()
        self.assertTrue(security_config["enable_pii_detection"])
        self.assertEqual(security_config["max_prompt_length"], 10000)

if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestOSSConfigurationLoader))
    test_suite.addTest(unittest.makeSuite(TestOSSConfigurationFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)