#!/bin/bash
# Setup required directories for MCP Associative Memory project
# This script ensures all necessary directories exist for CI/CD and testing

set -e

echo "🔧 Setting up project directories..."

# Create main data directories
mkdir -p data/{chroma_db,exports,imports,test,performance_test}

# Create log directories  
mkdir -p logs

# Create temporary directories
mkdir -p .copilot-temp

# Create test output directories
mkdir -p tests/{fixtures,outputs}

echo "✅ Directory structure created successfully"

# List created directories
echo "📁 Created directories:"
find data logs .copilot-temp tests -type d -name "[!.]*" 2>/dev/null | sort
