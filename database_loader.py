"""
Database loader for OSS edition
Handles PostgreSQL connection and API key management
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Database configuration from environment or defaults
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "wag_tail"),
    "user": os.getenv("DB_USER", "eddiechui"),
    "password": os.getenv("DB_PASSWORD", "Chinasky17_")
}

def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(
            **DB_CONFIG,
            cursor_factory=RealDictCursor
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Validate an API key against the database
    
    Args:
        api_key: The API key to validate
        
    Returns:
        Dict with key details if valid, None otherwise
    """
    if not api_key:
        return None
        
    conn = get_db_connection()
    if not conn:
        # Fallback to config file validation
        return validate_from_config(api_key)
    
    try:
        with conn.cursor() as cursor:
            # Check API key in database
            cursor.execute("""
                SELECT key, organization, org_id, is_active, 
                       rate_limit, monthly_limit, usage
                FROM api_keys 
                WHERE key = %s AND is_active = true
            """, (api_key,))
            
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            
    except psycopg2.Error as e:
        logger.error(f"Database query failed: {e}")
    finally:
        conn.close()
    
    # Fallback to config file
    return validate_from_config(api_key)

def validate_from_config(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fallback validation from config file
    
    Args:
        api_key: The API key to validate
        
    Returns:
        Dict with key details if valid, None otherwise
    """
    try:
        import yaml
        config_path = "config/sys_config.yaml"
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Check if key exists in config
            api_keys = config.get('security', {}).get('api_keys', {})
            
            for org_name, org_data in api_keys.items():
                if org_data.get('key') == api_key:
                    return {
                        'key': api_key,
                        'organization': org_name,
                        'org_id': org_data.get('org_id', org_name),
                        'is_active': True,
                        'rate_limit': org_data.get('rate_limit', 100),
                        'monthly_limit': org_data.get('monthly_limit', 10000)
                    }
                    
    except Exception as e:
        logger.error(f"Config file validation failed: {e}")
    
    return None

def init_database():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if not conn:
        logger.warning("Database not available - running in config-only mode")
        return False
    
    try:
        with conn.cursor() as cursor:
            # Create api_keys table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(255) UNIQUE NOT NULL,
                    organization VARCHAR(255) NOT NULL,
                    org_id VARCHAR(255),
                    is_active BOOLEAN DEFAULT true,
                    rate_limit INTEGER DEFAULT 100,
                    monthly_limit INTEGER DEFAULT 10000,
                    usage INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create usage_logs table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id SERIAL PRIMARY KEY,
                    api_key VARCHAR(255) NOT NULL,
                    endpoint VARCHAR(255),
                    method VARCHAR(10),
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    tokens_used INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Database tables initialized successfully")
            return True
            
    except psycopg2.Error as e:
        logger.error(f"Database initialization failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Initialize on module load
init_database()