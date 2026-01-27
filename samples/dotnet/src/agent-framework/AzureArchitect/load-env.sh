#!/bin/bash

# Load environment variables from .env file
# Usage: source ./load-env.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    return 1 2>/dev/null || exit 1
fi

# Export each line from .env file
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Export the variable
    export "$line"
done < "$ENV_FILE"

echo "Environment variables loaded from $ENV_FILE"
echo ""
echo "Available variables:"
echo "  AZURE_OPENAI_ENDPOINT: $AZURE_OPENAI_ENDPOINT"
echo "  AZURE_OPENAI_DEPLOYMENT_NAME: $AZURE_OPENAI_DEPLOYMENT_NAME"
echo "  MICROSOFT_FOUNDRY_PROJECT_ENDPOINT: $MICROSOFT_FOUNDRY_PROJECT_ENDPOINT"
echo "  MICROSOFT_FOUNDRY_PROJECT_DEPLOYMENT_NAME: $MICROSOFT_FOUNDRY_PROJECT_DEPLOYMENT_NAME"
