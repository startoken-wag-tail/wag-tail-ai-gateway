# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""
Wag Tail Basic Guard Plugin

Basic content filtering for OSS edition:
- Regex-based keyword filtering
- Code format detection 
- SQL injection protection
- System command blocking

This plugin provides essential security without AI/ML dependencies.
"""

from .basic_guard_plugin import WagTailBasicGuardPlugin

__version__ = "4.3.0"
__all__ = ["WagTailBasicGuardPlugin"]