#!/bin/bash

# NID Information Extraction API Run Script

set -e

echo "========================================="
echo "NID Information Extraction API"
echo "========================================="

# Check if .env file exists, if not copy from example
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
fi

# Create logs directory if it doesn't exist
if [ ! -d logs ]; then
    echo "Creating logs directory..."
    mkdir -p logs
    echo "✓ logs directory created"
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "========================================="
echo "Starting FastAPI server..."
echo "========================================="
echo ""

# Run the application
python main.py
