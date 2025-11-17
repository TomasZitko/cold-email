#!/bin/bash

# Professional Sales Automation System - Setup Script
# This script sets up a Python virtual environment and installs all dependencies

set -e  # Exit on error

echo "=========================================="
echo "🚀 PROFESSIONAL SALESMAN - SETUP"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.8+"; exit 1; }

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Create data directory if it doesn't exist
echo ""
echo "📁 Setting up data directory..."
mkdir -p data
echo "✅ Data directory ready"

# Check for .env file
echo ""
if [ -f ".env" ]; then
    echo "✅ .env file found"
else
    echo "⚠️  .env file not found"
    echo "📝 Creating .env from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file - PLEASE EDIT IT WITH YOUR CREDENTIALS!"
    else
        echo "❌ .env.example not found"
    fi
fi

# Summary
echo ""
echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials:"
echo "   nano .env"
echo ""
echo "2. Activate virtual environment (if not already active):"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the system:"
echo "   python main.py"
echo ""
echo "To deactivate virtual environment later:"
echo "   deactivate"
echo ""
echo "=========================================="
