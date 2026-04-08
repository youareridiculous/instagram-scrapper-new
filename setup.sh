#!/bin/bash

echo "🚀 Setting up Instagram Scraper..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers (scraper tries Firefox first, then Chromium)
echo "🌐 Installing Playwright browsers..."
playwright install firefox
playwright install chromium

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your Instagram credentials (use a separate account!)"
fi

# Create output directory
mkdir -p scraped_data

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Instagram credentials"
echo "2. Edit config.json to set your search criteria and filters"
echo "3. Run CLI: source venv/bin/activate && python instagram_scraper.py"
echo "   Or web UI: python web_interface.py  →  http://localhost:5001"
echo ""
echo "⚠️  Remember: Use a separate account, not your main account!"

