#!/bin/bash

# Issue Tracker API - Quick Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "=================================================="
echo "Issue Tracker API - Quick Setup"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Check PostgreSQL
echo "Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found. Make sure PostgreSQL is installed and running."
    echo "   You can install it with: brew install postgresql@14"
else
    echo "✓ PostgreSQL client found"
fi
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Setup environment file
echo "Setting up environment file..."
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Skipping..."
else
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your PostgreSQL credentials!"
    echo "   Default: postgresql+asyncpg://postgres:postgres@localhost:5432/issue_tracker"
fi
echo ""

# Create database (optional)
read -p "Do you want to create the PostgreSQL database? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating database..."
    createdb issue_tracker 2>/dev/null || echo "⚠️  Database might already exist or you need to create it manually"
    echo "✓ Database setup attempted"
fi
echo ""

# Initialize database
read -p "Do you want to initialize the database schema? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Initializing database..."
    python scripts/init_db.py
    echo "✓ Database initialized"
fi
echo ""

echo "=================================================="
echo "✓ Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Edit .env with your database credentials (if needed)"
echo "3. Start the server: uvicorn app.main:app --reload"
echo "4. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "Useful commands:"
echo "  - Run tests: pytest tests/ -v"
echo "  - Check code: ruff check app/"
echo "  - Format code: black app/"
echo "  - Type check: mypy app/"
echo ""
echo "=================================================="
