# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

# response_loader.py
import yaml

def load_responses(path="config/responses.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_error(name: str):
    data = load_responses()
    return data["errors"].get(name, {
        "status_code": 500,
        "message": "Unknown error"
    })
