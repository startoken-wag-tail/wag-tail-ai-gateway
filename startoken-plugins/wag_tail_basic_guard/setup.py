# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup, find_packages

setup(
    name="wag_tail_basic_guard",
    version="4.3.0",
    description="Basic content filtering for Wag Tail AI Gateway (OSS Edition)",
    packages=find_packages(),
    install_requires=[
        "regex>=2021.0.0",
    ],
    entry_points={
        'wag_tail_plugins': [
            'wag_tail_basic_guard = wag_tail_basic_guard.basic_guard_plugin:WagTailBasicGuardPlugin',
        ],
    },
    python_requires=">=3.8",
    author="Wag Tail Team",
    author_email="support@wagtail.ai",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)