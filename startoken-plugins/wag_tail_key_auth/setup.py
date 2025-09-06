# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup, find_packages

setup(
    name="wag_tail_key_auth",
    version="4.3.0",
    description="Wag-Tail AI Gateway plugin for API key authentication (cache + DB lookup)",
    author="wag_tail",
    packages=find_packages(),
    install_requires=[
        "redis",
        "sqlalchemy",
    ],
    python_requires=">=3.7",
    entry_points={
        "wag_tail_plugins": [
            "wag_tail_key_auth = wag_tail_key_auth.key_auth_plugin:WagTailKeyAuthPlugin"
        ]
    },
    include_package_data=True,
    zip_safe=False,
)
