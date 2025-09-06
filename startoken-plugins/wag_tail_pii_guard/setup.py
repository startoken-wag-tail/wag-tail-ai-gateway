# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup, find_packages

setup(
    name="wag_tail_pii_guard",
    version="4.3.0",
    description="Presidio-based PII detection plugin for Wag-tail AI Gateway",
    author="Team-C",
    packages=find_packages(),
    install_requires=[
        "presidio-analyzer",
        "presidio-anonymizer"
    ],
    python_requires='>=3.8',
    entry_points={
        'wag_tail_plugins': [
            'wag_tail_pii_guard = wag_tail_pii_guard.wag_tail_pii_guard:WagTailPIIGuard'
        ]
    }
)
