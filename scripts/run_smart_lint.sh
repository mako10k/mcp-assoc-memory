#!/bin/bash
"""
Wrapper script to run smart lint and replace existing VS Code tasks
"""

set -e

# Change to workspace directory
cd "$(dirname "$0")/.."

# Run smart lint
echo "🚀 Running Smart Lint System..."
echo "==============================================="

python scripts/smart_lint.py "$@"

exit_code=$?

echo ""
echo "📊 Smart Lint Results:"
echo "- Progress Log: .copilot-temp/smart-lint-progress.txt"
echo "- Detailed Report: .copilot-temp/smart-lint-report.txt"
echo ""

if [ $exit_code -eq 0 ]; then
    echo "✅ Smart lint completed successfully!"
else
    echo "❌ Smart lint found issues. Check reports for details."
fi

exit $exit_code
