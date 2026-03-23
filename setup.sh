#!/usr/bin/env bash
set -euo pipefail

echo "=== Argument Agent Setup ==="

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 10), f'Python 3.10+ required, got {sys.version}'" || {
    echo "Error: Python 3.10 or higher is required."
    exit 1
}

# 1. Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# 2. Activate
source .venv/bin/activate

# 3. Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# 4. ConnectOnion project (.co/) — same idea as browser-agent manual setup
if [ ! -f ".co/config.toml" ]; then
    echo ""
    echo "Initializing ConnectOnion project (co init)..."
    co init
fi

# 5. Authenticate ConnectOnion (interactive)
echo ""
echo "Authenticating ConnectOnion (co auth)..."
co auth

# 6. Build the law index (local embeddings by default)
echo ""
echo "Building NSW tenancy law index..."
python rag/build_index.py --local --rebuild

echo ""
echo "=== Setup complete ==="
echo ""
echo "Optional: cp .env.example .env for OPENONION_API_KEY / RAG vars (see README Environment)."
echo ""
echo "Start the backend with:"
echo "  source .venv/bin/activate"
echo "  uvicorn main:app --reload --port 8191"
