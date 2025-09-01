#!/bin/bash

# Wag-Tail AI Gateway OSS Edition
# Database Setup Script
# Copyright (c) 2025 Startoken Pty Ltd

set -e

echo "======================================"
echo "Wag-Tail AI Gateway - Database Setup"
echo "======================================"

# Default values
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-wag_tail}"
DB_USER="${DB_USER:-$USER}"

echo ""
echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    echo ""
    echo "Installation instructions:"
    echo "  macOS:    brew install postgresql"
    echo "  Ubuntu:   sudo apt-get install postgresql postgresql-contrib"
    echo "  CentOS:   sudo yum install postgresql-server postgresql-contrib"
    exit 1
fi

# Check if database exists
echo "Checking if database exists..."
if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "✅ Database '$DB_NAME' already exists"
else
    echo "Creating database '$DB_NAME'..."
    createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
    echo "✅ Database created successfully"
fi

# Run schema
echo ""
echo "Setting up database schema..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/schema.sql

echo ""
echo "✅ Database setup completed successfully!"
echo ""
echo "Test the setup with:"
echo "  psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c 'SELECT * FROM api_keys;'"
echo ""
echo "Your test API key is: sk-test-key-123"