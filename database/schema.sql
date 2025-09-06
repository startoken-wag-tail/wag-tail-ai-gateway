-- Wag-Tail AI Gateway OSS Edition
-- PostgreSQL Database Schema
-- Copyright (c) 2025 Startoken Pty Ltd
-- SPDX-License-Identifier: Apache-2.0

-- Create database if not exists (run as superuser)
-- CREATE DATABASE wag_tail;

-- API Keys table for authentication
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    organization VARCHAR(255) NOT NULL DEFAULT 'default',
    user_id VARCHAR(255),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_org ON api_keys(organization);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- Usage tracking table (optional but recommended)
CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER REFERENCES api_keys(id),
    organization VARCHAR(255),
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    request_tokens INTEGER,
    response_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for usage queries
CREATE INDEX IF NOT EXISTS idx_usage_logs_created ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_logs_org ON usage_logs(organization);

-- Insert default test API key for development
INSERT INTO api_keys (key, organization, description, is_active) 
VALUES ('demo-key-for-testing', 'default', 'Demo key for testing OSS edition', true)
ON CONFLICT (key) DO NOTHING;

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;