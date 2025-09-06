"""
Plugin loader for OSS edition
Loads only the basic security plugins included in OSS
"""

import os
import sys
import importlib
from pathlib import Path
from typing import List, Any

# Add plugins directory to path
plugins_dir = Path(__file__).parent / "startoken-plugins"
if str(plugins_dir) not in sys.path:
    sys.path.insert(0, str(plugins_dir))

# OSS Edition plugins
OSS_PLUGINS = [
    "wag_tail_key_auth",
    "wag_tail_basic_guard",
    "wag_tail_pii_guard"
]

def load_plugins() -> List[Any]:
    """Load OSS edition plugins"""
    plugins = []
    
    for plugin_name in OSS_PLUGINS:
        try:
            # Import the plugin module
            if plugin_name == "wag_tail_key_auth":
                from wag_tail_key_auth.key_auth_plugin import WagTailKeyAuthPlugin
                plugins.append(WagTailKeyAuthPlugin())
            elif plugin_name == "wag_tail_basic_guard":
                from wag_tail_basic_guard.basic_guard_plugin import WagTailBasicGuardPlugin
                plugins.append(WagTailBasicGuardPlugin())
            elif plugin_name == "wag_tail_pii_guard":
                from wag_tail_pii_guard.pii_guard_plugin import WagTailPIIGuardPlugin
                plugins.append(WagTailPIIGuardPlugin())
                
            print(f"✅ Loaded plugin: {plugin_name}")
            
        except ImportError as e:
            print(f"⚠️  Failed to load plugin {plugin_name}: {e}")
            
    return plugins

def get_user_edition() -> str:
    """Return OSS edition"""
    return "oss"
