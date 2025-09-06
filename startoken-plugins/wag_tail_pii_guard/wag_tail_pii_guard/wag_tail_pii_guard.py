# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.predefined_recognizers import (
    EmailRecognizer,
    PhoneRecognizer,
    CreditCardRecognizer,
    IbanRecognizer,
    UsSsnRecognizer,
    IpRecognizer,
    SpacyRecognizer,
    UsPassportRecognizer,
)
from presidio_anonymizer import AnonymizerEngine
from .hkid_recognizer import HKIDRecognizer

from wag_tail_logger import logger
from plugins.base import PluginBase
from pii_config_loader import get_allowed_pii_types, get_confidence_threshold

class WagTailPIIGuard(PluginBase):
    __version__ = "4.3.0"
    name = "wag_tail_pii_guard"
    description = "Presidio-based PII detection and masking for Wag-tail AI Gateway"

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        logger.info("[WagTailPIIGuard] Initialized Presidio Analyzer and Anonymizer.")

        # Explicitly register common recognizers to be sure
        self.analyzer.registry.add_recognizer(EmailRecognizer())
        self.analyzer.registry.add_recognizer(PhoneRecognizer())
        self.analyzer.registry.add_recognizer(CreditCardRecognizer())
        self.analyzer.registry.add_recognizer(IbanRecognizer())
        self.analyzer.registry.add_recognizer(UsSsnRecognizer())
        self.analyzer.registry.add_recognizer(HKIDRecognizer())
        self.analyzer.registry.add_recognizer(IpRecognizer())
        self.analyzer.registry.add_recognizer(UsPassportRecognizer())
        # Add SpacyRecognizer for PERSON detection
        # NOTE: SpacyRecognizer is expensive and causes performance issues
        # self.analyzer.registry.add_recognizer(SpacyRecognizer())

        # Print loaded recognizers for debugging
        # print("[DEBUG] Recognizers loaded:", [r.name for r in self.analyzer.get_recognizers(language="en")])

        self.allowed_pii_types = get_allowed_pii_types() or [
            "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "HK_ID", "US_PASSPORT",
            "BANK_ACCOUNT", "US_SSN", "NRIC", "NRIC_NUMBER", "IBAN_CODE", "PERSON", "IP_ADDRESS"
        ]
        self.confidence_threshold = get_confidence_threshold()

        # DEBUG: Print recognizer list at startup
        # try:
        #     recogs = self.analyzer.get_recognizers(language="en")
        #     print("[DEBUG] Presidio recognizers loaded:", [r.name for r in recogs])
        # except Exception as e:
        #     print("[DEBUG] Could not get Presidio recognizers:", e)

    def reload_config(self):
        """Reload configuration from YAML file for live updates"""
        try:
            # Reload allowed PII types
            new_allowed_types = get_allowed_pii_types()
            if new_allowed_types != self.allowed_pii_types:
                self.allowed_pii_types = new_allowed_types or [
                    "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "HK_ID", "US_PASSPORT",
                    "BANK_ACCOUNT", "US_SSN", "NRIC", "NRIC_NUMBER", "IBAN_CODE", "PERSON", "IP_ADDRESS"
                ]
                logger.info(f"[WagTailPIIGuard] Updated allowed PII types: {self.allowed_pii_types}")
            
            # Reload confidence threshold
            new_threshold = get_confidence_threshold()
            if new_threshold != self.confidence_threshold:
                old_threshold = self.confidence_threshold
                self.confidence_threshold = new_threshold
                logger.info(f"[WagTailPIIGuard] Updated confidence threshold: {old_threshold} -> {new_threshold}")
        except Exception as e:
            # If reload fails, keep existing configuration
            logger.warning(f"[WagTailPIIGuard] Failed to reload config: {e}")

    def scan_for_pii(self, text, language='en'):
        # Handle null/empty input
        if text is None:
            raise TypeError("Cannot scan None text for PII")
        if not text or not text.strip():
            return []
        
        # DEBUG: Show recognizers every call (for troubleshooting)
        # try:
        #     recogs = self.analyzer.get_recognizers(language=language)
        #     print("[DEBUG] Recognizers:", [r.name for r in recogs])
        # except Exception as e:
        #     print("[DEBUG] Could not get recognizers:", e)

        results = self.analyzer.analyze(text=text, language=language)
        # print("[DEBUG] Presidio raw results:", results)
        findings = [
            {
                "entity_type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": r.score,
                "text": text[r.start:r.end]
            }
            for r in results
            if r.entity_type in self.allowed_pii_types and r.score >= self.confidence_threshold
        ]
        logger.debug(
            f"[WagTailPIIGuard] scan_for_pii: Found {len(findings)} entities "
            f"(types: {[f['entity_type'] for f in findings]}) in text: '{text[:40]}...'"
        )
        if findings:
            logger.info(f"[WagTailPIIGuard] Detected PII: {[f['entity_type'] for f in findings]}")
        # print("PII findings:", findings)
        return findings

    def mask_pii(self, text, language='en', mask_char='*'):
        from presidio_anonymizer.entities import OperatorConfig
        
        # Handle null/empty input
        if text is None:
            raise TypeError("Cannot mask PII in None text")
        if not text or not text.strip():
            return text
        
        results = self.analyzer.analyze(text=text, language=language)
        if not results:
            logger.debug("[WagTailPIIGuard] mask_pii: No PII found.")
            return text
        logger.info(f"[WagTailPIIGuard] mask_pii: Masking {len(results)} PII entities in text.")
        
        # Create operators dict with OperatorConfig objects
        operators = {}
        for r in results:
            operators[r.entity_type] = OperatorConfig(
                "replace", 
                {"new_value": mask_char * (r.end - r.start)}
            )
        
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        logger.debug(f"[WagTailPIIGuard] mask_pii: Masked text: '{anonymized_result.text[:40]}...'")
        return anonymized_result.text

    def on_request(self, request, context):
        # Reload configuration on each request for live updates
        self.reload_config()
        
        # Handle null context
        if context is None:
            return None
            
        # Check for messages in context (modern format)
        messages = context.get("messages", [])
        if messages:
            for msg in messages:
                content = msg.get("content", "")
                if content:
                    findings = self.scan_for_pii(content)
                    if findings:
                        # Create detailed block reason with recognizer info
                        pii_types = [f["entity_type"] for f in findings]
                        pii_types_str = ", ".join(pii_types)
                        block_reason = f"PII detected ({pii_types_str})"
                        
                        logger.warning(f"[WagTailPIIGuard] Blocking message with PII: {pii_types}")
                        return {
                            "response": {"prompt": ""},
                            "flag": "blocked",
                            "reason": block_reason,
                            "classified_type": "pii",
                            "pii_entities": pii_types,
                            "pii_examples": [f["text"] for f in findings]
                        }
            context["pii_detected"] = False
            return None
            
        # Fallback to prompt field (legacy format)
        prompt = context.get("prompt")
        if not prompt:
            return None
        findings = self.scan_for_pii(prompt)
        if findings:
            logger.warning(f"[WagTailPIIGuard] Blocking prompt with PII: {findings}")
            # Create detailed block reason with recognizer info
            pii_types = [f["entity_type"] for f in findings]
            pii_types_str = ", ".join(pii_types)
            block_reason = f"PII detected ({pii_types_str})"
            
            return {
                "response": {"prompt": ""},
                "flag": "blocked",
                "reason": block_reason,
                "classified_type": "pii",
                "pii_entities": pii_types,
                "pii_examples": [f["text"] for f in findings]
            }
        return None  # Allow prompt through if no PII detected
    
    def on_response(self, request, context, response):
        # Handle response masking - note: added 'request' parameter to match expected signature
        if response and hasattr(response, 'content'):
            try:
                findings = self.scan_for_pii(response.content)
                if findings:
                    logger.info(f"[WagTailPIIGuard] Found PII in response, masking...")
                    masked_content = self.mask_pii(response.content)
                    # Create new response object with masked content
                    from copy import deepcopy
                    masked_response = deepcopy(response)
                    masked_response.content = masked_content
                    return masked_response
            except Exception as e:
                logger.error(f"[WagTailPIIGuard] Error in on_response: {e}")
        return response
