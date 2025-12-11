#!/bin/bash
# Quick setup script for the Workflow Engine

echo "🚀 Setting up Workflow Engine..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
pytest tests/test_engine.py -v --tb=short

# Start server
echo "🎉 Setup complete!"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Then visit: http://localhost:8000/docs"
