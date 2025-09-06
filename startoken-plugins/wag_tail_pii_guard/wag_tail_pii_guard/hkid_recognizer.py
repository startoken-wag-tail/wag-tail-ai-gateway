# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

from presidio_analyzer import Pattern, PatternRecognizer

class HKIDRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern("hkid_pattern", r"[A-Z]{1,2}\d{6}\([0-9A]\)", 0.8),
        ]
        super().__init__(
            supported_entity="HK_ID",
            name="HKID Recognizer",
            patterns=patterns,
            context=["HKID", "Hong Kong Identity Card", "身份證"],
        )
