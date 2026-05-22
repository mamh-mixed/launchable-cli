#!/bin/bash
# Update the bundled OpenAPI schema from mothership dev server
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$(dirname "$SCRIPT_DIR")"
SCHEMA_FILE="$CLI_DIR/smart_tests/schema/openapi-schema.json"

echo "Fetching OpenAPI schema from local dev server..."

# Check if mothership is running
if ! curl -s -f http://localhost:8080/intake/v3/api-docs > /dev/null 2>&1; then
    echo "Error: Mothership dev server not running at localhost:8080"
    echo "Please start it with: cd mothership && bazel run //src/main/java/com/launchableinc/mercury/intake"
    exit 1
fi

# Create schema directory if it doesn't exist
mkdir -p "$(dirname "$SCHEMA_FILE")"

# Fetch and save schema
curl -s http://localhost:8080/intake/v3/api-docs > "$SCHEMA_FILE"

# Validate it's valid JSON
if ! python3 -m json.tool "$SCHEMA_FILE" > /dev/null 2>&1; then
    echo "Error: Downloaded file is not valid JSON"
    exit 1
fi

echo "✓ Schema updated successfully: $SCHEMA_FILE"
echo ""

# Show what changed
if git diff --quiet "$SCHEMA_FILE" 2>/dev/null; then
    echo "No changes detected in schema"
else
    echo "Changes detected:"
    git diff --stat "$SCHEMA_FILE" 2>/dev/null || echo "(Not a git repository)"
    echo ""
    echo "Review with: git diff $SCHEMA_FILE"
    echo "Commit with: git add $SCHEMA_FILE && git commit -m 'Update OpenAPI schema'"
fi
