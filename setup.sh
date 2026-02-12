#!/bin/bash
# Bin-Xray Setup Script
# Automatically sets up the development environment

set -e  # Exit on error

echo "╔════════════════════════════════════════════════╗"
echo "║     Bin-Xray Development Environment Setup    ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Check system dependencies
echo "🔍 Checking system dependencies..."
MISSING_TOOLS=()

for tool in readelf nm objdump ar; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS+=($tool)
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "⚠️  Missing tools: ${MISSING_TOOLS[*]}"
    echo ""
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install binutils file python3-tk python3-venv"
    echo "  Fedora/RHEL:   sudo dnf install binutils file python3-tkinter python3-venv"
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ All binary analysis tools found"
fi
echo ""

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  Virtual environment already exists at .venv"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        echo "✓ Virtual environment recreated"
    else
        echo "✓ Using existing virtual environment"
    fi
else
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo "✓ Dependencies installed:"
    pip list | grep -E "networkx"
else
    echo "❌ requirements.txt not found"
    exit 1
fi
echo ""

# Run verification test
echo "🧪 Running verification tests..."
echo ""
if [ -f "scripts/test_installation.py" ]; then
    python3 scripts/test_installation.py
else
    echo "⚠️  Test script not found, skipping verification"
fi
echo ""

echo "╔════════════════════════════════════════════════╗"
echo "║            Setup Complete! 🎉                  ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run Bin-Xray:"
echo "  python3 bin_xray.py"
echo ""
echo "To deactivate the virtual environment:"
echo "  deactivate"
echo ""
