# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""
Database connection and authentication for OSS Edition
"""

import os
import logging
from typing import Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config_loader import load_config

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manages PostgreSQL database connection"""
    
    def __init__(self):
        self.engine = None
        self.config = load_config().get("database", {})
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection"""
        try:
            # Get database configuration
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 5432)
            db_name = self.config.get("name", "wag_tail")
            
            # Handle user and password with environment variable fallback
            user = os.getenv("DB_USER", os.getenv("USER", "postgres"))
            if "${DB_USER}" in str(self.config.get("user", "")):
                user = os.getenv("DB_USER", os.getenv("USER", "postgres"))
            else:
                user = self.config.get("user", user)
            
            password = os.getenv("DB_PASSWORD", "")
            if "${DB_PASSWORD}" in str(self.config.get("password", "")):
                password = os.getenv("DB_PASSWORD", "")
            else:
                password = self.config.get("password", "")
            
            # Build connection string
            if password:
                conn_str = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
            else:
                conn_str = f"postgresql://{user}@{host}:{port}/{db_name}"
            
            # Create engine with connection pooling
            self.engine = create_engine(
                conn_str,
                pool_size=self.config.get("pool_size", 5),
                max_overflow=self.config.get("max_overflow", 10),
                pool_pre_ping=True,  # Verify connections before use
                echo=False  # Set to True for SQL debugging
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            logger.info(f"✅ Database connected successfully to {db_name}@{host}")
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Database connection failed: {e}")
            logger.warning("System will use configuration file fallback for API keys")
            self.engine = None
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to database: {e}")
            self.engine = None
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate API key against database
        
        Returns:
            Tuple of (is_valid, organization, user_id)
        """
        if not self.engine or not api_key:
            return False, None, None
        
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT organization, user_id, is_active 
                    FROM api_keys 
                    WHERE key = :api_key
                    AND is_active = true
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """)
                
                result = conn.execute(query, {"api_key": api_key})
                row = result.fetchone()
                
                if row:
                    organization, user_id, is_active = row
                    
                    # Update last_used_at
                    try:
                        update_query = text("""
                            UPDATE api_keys 
                            SET last_used_at = CURRENT_TIMESTAMP 
                            WHERE key = :api_key
                        """)
                        conn.execute(update_query, {"api_key": api_key})
                        conn.commit()
                    except:
                        pass  # Don't fail on update
                    
                    logger.debug(f"API key validated: {api_key[-6:]}")
                    return True, organization, user_id
                
        except SQLAlchemyError as e:
            logger.error(f"Database error during API key validation: {e}")
        
        return False, None, None
    
    def log_usage(self, api_key: str, endpoint: str, method: str, 
                  status_code: int, latency_ms: int):
        """Log API usage to database"""
        if not self.engine:
            return
        
        try:
            with self.engine.connect() as conn:
                # Get API key ID
                key_query = text("SELECT id, organization FROM api_keys WHERE key = :api_key")
                key_result = conn.execute(key_query, {"api_key": api_key})
                key_row = key_result.fetchone()
                
                if key_row:
                    api_key_id, organization = key_row
                    
                    # Insert usage log
                    insert_query = text("""
                        INSERT INTO usage_logs 
                        (api_key_id, organization, endpoint, method, status_code, latency_ms)
                        VALUES (:api_key_id, :organization, :endpoint, :method, :status_code, :latency_ms)
                    """)
                    
                    conn.execute(insert_query, {
                        "api_key_id": api_key_id,
                        "organization": organization,
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": status_code,
                        "latency_ms": latency_ms
                    })
                    conn.commit()
                    
        except SQLAlchemyError as e:
            logger.debug(f"Failed to log usage: {e}")

# Global database connection instance
_db_connection = None

def get_db_connection() -> DatabaseConnection:
    """Get or create database connection"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection

def validate_api_key(api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate API key with database fallback to config
    
    Returns:
        Tuple of (is_valid, organization, user_id)
    """
    # Try database first
    db = get_db_connection()
    is_valid, org, user = db.validate_api_key(api_key)
    
    if is_valid:
        return True, org, user
    
    # Fallback to config file (for test key)
    config = load_config()
    test_keys = config.get("auth", {}).get("test_keys", [])
    
    if api_key in test_keys or api_key == "sk-test-key-123":
        logger.debug(f"API key validated from config: {api_key[-6:]}")
        return True, "default", "test_user"
    
    return False, None, None