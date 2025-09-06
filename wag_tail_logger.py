# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import yaml
import sys
import warnings
import traceback
from logging.handlers import RotatingFileHandler

# === CONFIG ===
CONFIG_PATH = "config/sys_config.yaml"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "logs/wag_tail_gateway.log"
DEFAULT_MAX_LOG_SIZE_MB = 20
DEFAULT_BACKUP_COUNT = 10

def get_log_config():
    log_level = DEFAULT_LOG_LEVEL
    log_file = DEFAULT_LOG_FILE
    max_log_size_mb = DEFAULT_MAX_LOG_SIZE_MB
    backup_count = DEFAULT_BACKUP_COUNT

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = yaml.safe_load(f)
                log_cfg = config.get("log", {})
                log_level = log_cfg.get("log_level", DEFAULT_LOG_LEVEL).upper()
                log_file = log_cfg.get("gateway_log", log_file)
                max_log_size_mb = log_cfg.get("max_log_size_mb", max_log_size_mb)
                backup_count = log_cfg.get("backup_count", backup_count)
        except Exception as e:
            print(f"Could not load logging config from YAML: {e}")

    # Print out the log level loaded for debugging
    print(f"[WAG_TAIL LOGGER] Using log_level: {log_level}, log_file: {log_file}")
    return log_level, log_file, max_log_size_mb, backup_count

log_level_str, log_path, max_log_size_mb, backup_count = get_log_config()
log_level = getattr(logging, log_level_str, logging.INFO)

# === ENSURE LOG DIRECTORY ===
log_dir = os.path.dirname(log_path)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

# === HANDLERS AND FORMATTERS ===
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

file_handler = RotatingFileHandler(
    log_path,
    maxBytes=max_log_size_mb * 1024 * 1024,
    backupCount=backup_count,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# === MAIN LOGGER ===
logger = logging.getLogger("wag_tail")

# Clear any existing handlers (avoid duplication on reloads)
if logger.hasHandlers():
    logger.handlers.clear()

logger.setLevel(log_level)
logger.addHandler(file_handler)
logger.addHandler(console_handler)  # Remove this if you do NOT want console logs

# === CAPTURE WARNINGS AND UNCAUGHT EXCEPTIONS ===

def setup_comprehensive_logging():
    """Set up comprehensive logging to capture all errors and warnings"""
    
    # 1. Capture Python warnings to logger
    logging.captureWarnings(True)
    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.addHandler(file_handler)
    warnings_logger.setLevel(logging.WARNING)
    
    # 2. Redirect stderr to logger for uncaught exceptions
    class StderrToLogger:
        def __init__(self, logger, level=logging.ERROR):
            self.logger = logger
            self.level = level
            self.linebuf = ''

        def write(self, buf):
            temp_linebuf = self.linebuf + buf
            self.linebuf = ''
            for line in temp_linebuf.splitlines(True):
                if line[-1] == '\n':
                    # Complete line - log it
                    if line.strip():  # Don't log empty lines
                        self.logger.log(self.level, line.rstrip())
                else:
                    # Incomplete line - buffer it
                    self.linebuf = line

        def flush(self):
            if self.linebuf:
                self.logger.log(self.level, self.linebuf.rstrip())
                self.linebuf = ''

    # 3. Set up global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow KeyboardInterrupt to exit normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log all other uncaught exceptions
        logger.critical(
            "Uncaught exception", 
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    # Install the exception handler
    sys.excepthook = handle_exception
    
    # 4. Optionally redirect stderr (be careful - this affects all stderr output)
    # Uncomment the next line if you want ALL stderr to go to logs
    # sys.stderr = StderrToLogger(logger, logging.ERROR)
    
    logger.info("Comprehensive logging setup completed")

# Set up comprehensive logging
setup_comprehensive_logging()

wag_tail_logger = logger

def get_logger():
    """For backward compatibility if needed elsewhere."""
    return wag_tail_logger
