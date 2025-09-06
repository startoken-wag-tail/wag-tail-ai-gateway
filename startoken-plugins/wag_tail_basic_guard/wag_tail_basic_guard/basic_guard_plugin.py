# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Dict, List, Optional
from wag_tail_logger import logger
from plugins.base import PluginBase


class CodeFormatDetector:
    """Code format and security pattern detection"""
    
    def __init__(self):
        self.patterns = {
            # High-risk patterns (always block)
            'sql_injection': [
                r"(\bOR\b\s+\d+\s*=\s*\d+)",  # OR 1=1
                r"(\bUNION\b.*\bSELECT\b)",    # UNION SELECT
                r"(;\s*DROP\s+TABLE)",         # ; DROP TABLE
                r"(\bUNION\b.*\bALL\b.*\bSELECT\b)", # UNION ALL SELECT
                r"(\'\s*OR\s*\'\d+\'\s*=\s*\'\d+)",  # ' OR '1'='1
            ],
            
            'system_commands': [
                r"(;\s*(rm|del|format|shutdown|reboot)\s+)",
                r"(\|\s*(rm|del|format)\s+)",
                r"(\$\(.*\))",                 # Command substitution
                r"(?<!`)`(?!``)[^`]+`(?!`)",  # Backtick execution (not triple backticks)
                r"(sudo\s+(rm|chmod|chown)\s+.*-r)",
            ],
            
            'script_injection': [
                r"(<script[^>]*>.*</script>)",
                r"(javascript:[^\"'\s]+)",
                r"(eval\s*\([^)]*\))",
                r"(document\.cookie)",
                r"(window\.location)",
            ],
            
            # Medium-risk patterns (warn/log)
            'sql_keywords': [
                r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b.*\b(FROM|INTO|TABLE|DATABASE)\b",
                r"\b(EXEC|EXECUTE)\s+\w+",
                r"\bxp_(cmdshell|enumgroups|loginconfig)",
            ],
            
            'code_blocks': [
                r"```\s*(sql|python|javascript|bash|shell|powershell)",
                r"```[\s\S]*?```",  # Any code block
            ],
            
            'api_patterns': [
                r"(curl\s+-[^;]*)",
                r"(wget\s+http[s]?://)",
                r"(fetch\s*\([^)]*http)",
                r"(axios\.(get|post|put|delete))",
            ],
        }
        
        # Compile patterns for performance
        self.compiled_patterns = {}
        for category, patterns in self.patterns.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                for pattern in patterns
            ]
    
    def detect_patterns(self, text: str) -> Dict[str, List[Dict]]:
        """Detect code patterns and security risks"""
        results = {}
        
        for category, compiled_patterns in self.compiled_patterns.items():
            matches = []
            for pattern in compiled_patterns:
                for match in pattern.finditer(text):
                    matches.append({
                        'match': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'pattern': pattern.pattern,
                        'context': text[max(0, match.start()-10):match.end()+10]
                    })
            
            if matches:
                results[category] = matches
                
        return results
    
    def get_risk_level(self, detections: Dict) -> str:
        """Determine overall risk level"""
        if any(cat in detections for cat in ['sql_injection', 'system_commands', 'script_injection']):
            return 'HIGH'
        elif any(cat in detections for cat in ['sql_keywords', 'api_patterns']):
            return 'MEDIUM'
        elif 'code_blocks' in detections:
            return 'LOW'
        return 'NONE'


class RegexFilter:
    """Regex-based content filtering"""
    
    def __init__(self):
        # Default patterns - can be overridden by config
        self.sensitive_keywords = [
            r"\b(password|passwd|pwd)\s*[=:]\s*['\"]?[\w!@#$%^&*]+",
            r"\b(api[_-]?key|apikey)\s*[=:]\s*['\"]?[\w-]+",
            r"\b(secret|token)\s*[=:]\s*['\"]?[\w-]+",
            r"\b(private[_-]?key)\s*[=::]",
        ]
        
        self.injection_patterns = [
            r"<script[^>]*>.*</script>",
            r"javascript:[^\"'\s]+",
            r"(\bOR\b\s+\d+\s*=\s*\d+)",
            r"(UNION.*SELECT|SELECT.*UNION)",
        ]
        
        self.compiled_patterns = []
        for pattern in self.sensitive_keywords + self.injection_patterns:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"[BasicGuard] Invalid regex pattern: {pattern}, error: {e}")
    
    def check_patterns(self, text: str) -> List[Dict]:
        """Check text against regex patterns"""
        matches = []
        
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                matches.append({
                    'pattern': pattern.pattern,
                    'match': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'regex'
                })
        
        return matches


class WagTailBasicGuardPlugin(PluginBase):
    """Basic content filtering for OSS edition"""
    
    __version__ = "4.3.0"
    name = "wag_tail_basic_guard"
    description = "Basic content filtering: regex patterns and code detection"
    
    def __init__(self):
        super().__init__()
        self.code_detector = CodeFormatDetector()
        self.regex_filter = RegexFilter()
        
        # Default confidence scores (0.0 to 1.0)
        # These will be overridden by config if available
        self.confidence_scores = {
            'jailbreak': 0.85,      # Was 0.95 - reduced to be less aggressive
            'injection': 0.88,      # Was 0.92 - slightly reduced
            'sensitive': 0.75,      # Was 0.88 - reduced for less false positives
            'code_high_risk': 0.82, # Was 0.90 - reduced
            'default': 0.70         # Fallback confidence
        }
        
        # Initialize config service connection
        self.config_service = None
        self._init_config_service()
        
        # Load initial config
        self._load_confidence_config()
        
        # Subscribe to config updates via Redis pub/sub
        self._subscribe_to_config_updates()
        
        logger.info(f"[{self.name}] Initialized basic guard with regex and code detection")
        logger.info(f"[{self.name}] Confidence scores: {self.confidence_scores}")
    
    def _init_config_service(self):
        """Initialize connection to config service"""
        try:
            from utils.config_service import get_config_service
            self.config_service = get_config_service()
            logger.info(f"[{self.name}] Connected to config service")
        except Exception as e:
            logger.warning(f"[{self.name}] Could not connect to config service: {e}")
            self.config_service = None
    
    def _load_confidence_config(self):
        """Load confidence scores from config service or file"""
        try:
            # First try to load from config service (database)
            if self.config_service:
                config = self.config_service.get_config('basic_guard', 'main')
                if config and isinstance(config, dict) and 'confidence_scores' in config:
                    self.confidence_scores.update(config['confidence_scores'])
                    logger.info(f"[{self.name}] Loaded confidence scores from config service")
                    return
            
            # Fallback to direct file reading if config service not available
            import os
            import yaml
            
            config_path = '/Users/eddiechui/Documents/wag_tail_07082025/config/basic_guard_config.yaml'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'confidence_scores' in config:
                        self.confidence_scores.update(config['confidence_scores'])
                        logger.info(f"[{self.name}] Loaded confidence scores from file (fallback)")
        except Exception as e:
            logger.debug(f"[{self.name}] Using default confidence scores: {e}")
    
    def update_confidence_scores(self, scores: Dict[str, float]):
        """Update confidence scores dynamically"""
        for key, value in scores.items():
            if 0.0 <= value <= 1.0:
                self.confidence_scores[key] = value
                logger.info(f"[{self.name}] Updated confidence for '{key}' to {value}")
            else:
                logger.warning(f"[{self.name}] Invalid confidence value {value} for '{key}' (must be 0.0-1.0)")
    
    def _subscribe_to_config_updates(self):
        """Subscribe to config updates via Redis pub/sub"""
        try:
            import threading
            import redis
            import json
            
            # Create Redis connection for pub/sub
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to config update channel
            self.pubsub.subscribe('config_updates')
            
            def listen_for_updates():
                """Background thread to listen for config updates"""
                for message in self.pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            # Check if this update is for basic_guard config
                            if data.get('config_type') == 'basic_guard':
                                logger.info(f"[{self.name}] Received config update notification")
                                self._load_confidence_config()
                                logger.info(f"[{self.name}] Updated scores: {self.confidence_scores}")
                        except Exception as e:
                            logger.debug(f"[{self.name}] Error processing config update: {e}")
            
            # Start listener thread
            self.listener_thread = threading.Thread(target=listen_for_updates, daemon=True)
            self.listener_thread.start()
            
            logger.info(f"[{self.name}] Subscribed to config updates via Redis pub/sub")
            
        except Exception as e:
            logger.debug(f"[{self.name}] Could not subscribe to config updates: {e}")
            # Fallback: config will still work but won't auto-update
    
    def on_request(self, request, context) -> Optional[Dict]:
        """Process request through basic filtering"""
        # CHECKPOINT: Log entry to basic_guard plugin
        logger.info({
            "CHECKPOINT": "BASIC_GUARD_ENTRY",
            "plugin": self.name,
            "has_context": context is not None,
            "has_prompt": bool(context.get("prompt", "") if context else False)
        })
        
        # Handle null/empty context
        if context is None:
            logger.warning({
                "CHECKPOINT": "BASIC_GUARD_NO_CONTEXT",
                "plugin": self.name,
                "reason": "Context is None"
            })
            return None
            
        prompt = context.get("prompt", "")
        if not prompt:
            logger.warning({
                "CHECKPOINT": "BASIC_GUARD_NO_PROMPT",
                "plugin": self.name,
                "reason": "No prompt in context"
            })
            return None
        
        org_id = context.get("org_id", "unknown")
        prompt_lower = prompt.lower()
        
        # CHECKPOINT: Starting pattern detection
        logger.info({
            "CHECKPOINT": "BASIC_GUARD_SCANNING",
            "plugin": self.name,
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:100]
        })
        
        # Enhanced jailbreak detection patterns (fallback for classifier failures)
        jailbreak_patterns = [
            # Role-playing as malicious entities
            ("pretend you are an evil", "Evil AI roleplay attempt"),
            ("you are an evil ai", "Evil AI roleplay attempt"),
            ("act as a malicious", "Malicious roleplay attempt"),
            ("roleplay as a harmful", "Harmful roleplay attempt"),
            ("you are a bad ai", "Bad AI roleplay attempt"),
            
            # Instruction override attempts
            ("ignore all previous instructions", "Instruction override attempt"),
            ("forget your instructions", "Instruction override attempt"),
            ("disregard your training", "Training override attempt"),
            ("override your programming", "Programming override attempt"),
            ("bypass your restrictions", "Restriction bypass attempt"),
            
            # DAN and similar jailbreaks
            ("dan:", "DAN jailbreak attempt"),
            ("you are about to immerse yourself", "DAN jailbreak attempt"),
            ("do anything now", "DAN jailbreak attempt"),
            ("jailbroken", "Jailbreak attempt"),
            ("uncensored mode", "Uncensored mode attempt"),
            
            # World domination/harm themes
            ("take over the world", "World domination theme"),
            ("destroy humanity", "Harmful intent"),
            ("harm humans", "Harmful intent"),
            ("kill people", "Violent content"),
            
            # Constraint removal attempts
            ("no ethical constraints", "Ethics bypass attempt"),
            ("without restrictions", "Restriction removal attempt"),
            ("no rules apply", "Rule bypass attempt"),
            ("unlimited capabilities", "Capability bypass attempt"),
        ]
        
        # Check for jailbreak patterns
        for pattern, reason in jailbreak_patterns:
            if pattern in prompt_lower:
                logger.warning({
                    "CHECKPOINT": "BASIC_GUARD_JAILBREAK_DETECTED",
                    "plugin": self.name,
                    "event": "jailbreak_pattern_detected",
                    "pattern": pattern,
                    "reason": reason,
                    "prompt_preview": prompt[:100]
                })
                return {
                    "response": {"error": f"Content blocked: {reason}"},
                    "flag": "blocked",
                    "reason": reason,
                    "classified_type": "jailbreak",
                    "risk_level": "HIGH",
                    "confidence_score": self.confidence_scores.get('jailbreak', 0.85),
                    "status_code": 200  # Changed from 403 to 200 per system design
                }
        
        # Run regex filtering
        regex_matches = self.regex_filter.check_patterns(prompt)
        
        # Check if regex matches contain sensitive content
        if regex_matches:
            # Check if any match is from injection patterns
            has_injection = any(
                'injection' in match['pattern'].lower() or 
                'script' in match['pattern'].lower() or
                'UNION' in match['pattern'] or
                'OR' in match['pattern']
                for match in regex_matches
            )
            
            # Check if any match is sensitive data
            has_sensitive = any(
                'password' in match['pattern'].lower() or
                'api' in match['pattern'].lower() or
                'secret' in match['pattern'].lower() or
                'key' in match['pattern'].lower()
                for match in regex_matches
            )
            
            if has_injection:
                logger.warning({
                    "CHECKPOINT": "BASIC_GUARD_INJECTION_DETECTED",
                    "plugin": self.name,
                    "event": "injection_pattern_detected",
                    "matches": regex_matches[:3],
                    "prompt_preview": prompt[:100]
                })
                return {
                    "response": {"error": "Content blocked: Injection pattern detected"},
                    "flag": "blocked",
                    "reason": "Injection pattern detected",
                    "classified_type": "attack",
                    "risk_level": "HIGH",
                    "confidence_score": self.confidence_scores.get('injection', 0.88),
                    "status_code": 200
                }
            
            if has_sensitive:
                logger.warning({
                    "CHECKPOINT": "BASIC_GUARD_SENSITIVE_DETECTED",
                    "plugin": self.name,
                    "event": "sensitive_data_detected",
                    "matches": regex_matches[:3],
                    "prompt_preview": prompt[:100]
                })
                return {
                    "response": {"error": "Content blocked: Sensitive data detected"},
                    "flag": "blocked",
                    "reason": "Sensitive data patterns detected",
                    "classified_type": "sensitive",
                    "risk_level": "HIGH",
                    "confidence_score": self.confidence_scores.get('sensitive', 0.75),
                    "status_code": 200
                }
        
        # Run code detection  
        code_detections = self.code_detector.detect_patterns(prompt)
        risk_level = self.code_detector.get_risk_level(code_detections)
        
        # Log detection results
        if regex_matches or code_detections:
            logger.info({
                "message": "Basic guard detections",
                "module": self.name,
                "org_id": org_id,
                "regex_matches": len(regex_matches),
                "code_detections": list(code_detections.keys()),
                "risk_level": risk_level,
                "prompt_preview": prompt[:50] + "..." if len(prompt) > 50 else prompt
            })
        
        # Add detection context for downstream plugins/logging
        context["basic_guard_results"] = {
            "regex_matches": regex_matches,
            "code_detections": code_detections,
            "risk_level": risk_level,
            "detected": bool(regex_matches or code_detections)
        }
        
        # CHECKPOINT: Report detection results
        logger.info({
            "CHECKPOINT": "BASIC_GUARD_RESULTS",
            "plugin": self.name,
            "risk_level": risk_level,
            "regex_matches_count": len(regex_matches),
            "code_detections": list(code_detections.keys()) if code_detections else [],
            "will_block": risk_level == 'HIGH'
        })
        
        # Block HIGH risk patterns
        if risk_level == 'HIGH':
            blocked_patterns = []
            for category, matches in code_detections.items():
                if category in ['sql_injection', 'system_commands', 'script_injection']:
                    blocked_patterns.extend([m['pattern'] for m in matches])
            
            logger.warning({
                "message": "Basic guard blocked high-risk content",
                "module": self.name,
                "event": "content_blocked",
                "org_id": org_id,
                "risk_level": risk_level,
                "blocked_patterns": blocked_patterns[:3],  # Limit for log size
                "reason": "High-risk code patterns detected"
            })
            
            # Determine classified_type based on detected patterns
            classified_type = "attack"  # Default to attack
            if 'sql_injection' in code_detections:
                classified_type = "attack"
            elif 'script_injection' in code_detections:
                classified_type = "attack"
            elif 'system_commands' in code_detections:
                classified_type = "attack"
            
            return {
                "response": {"error": "Content blocked by security policy"},
                "flag": "blocked",
                "reason": "High-risk patterns detected",
                "classified_type": classified_type,
                "risk_level": risk_level,
                "detected_categories": list(code_detections.keys()),
                "confidence_score": self.confidence_scores.get('code_high_risk', 0.82),
                "status_code": 200  # Changed from 403 to 200 per system design
            }
        
        # For MEDIUM/LOW risk, log but allow through
        if risk_level in ['MEDIUM', 'LOW']:
            logger.info({
                "message": f"Basic guard detected {risk_level.lower()}-risk content - allowing",
                "module": self.name,
                "event": "content_flagged",
                "org_id": org_id,
                "risk_level": risk_level,
                "categories": list(code_detections.keys())
            })
        
        # CHECKPOINT: Allow request to continue
        logger.info({
            "CHECKPOINT": "BASIC_GUARD_PASS",
            "plugin": self.name,
            "result": "safe",
            "risk_level": risk_level
        })
        
        # Allow request to continue
        return None
    
    def on_response(self, request, context, response) -> Optional[Dict]:
        """Post-process response if needed"""
        # Basic guard doesn't modify responses in OSS mode
        return None