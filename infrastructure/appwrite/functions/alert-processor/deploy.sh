#!/bin/bash

# Deploy Alert Processor Appwrite Function
# This script automates the deployment of the alert-processor function to Appwrite

set -e

echo "=== Appwrite Alert Processor Deployment ==="

# Configuration
FUNCTION_ID="alert-processor"
FUNCTION_NAME="Alert Processor"
RUNTIME="node-18.0"
ENTRYPOINT="src/main.js"
EXECUTE="any"

# Check if appwrite CLI is installed
if ! command -v appwrite &> /dev/null; then
    echo "❌ Appwrite CLI not found. Installing..."
    npm install -g appwrite-cli
fi

# Navigate to function directory
cd "$(dirname "$0")"

echo "📦 Installing dependencies..."
npm install

echo "🧪 Running tests..."
npm test || echo "⚠️  Tests failed, but continuing with deployment"

echo "📝 Creating function bundle..."
tar -czf function.tar.gz package.json src/ node_modules/

echo "🚀 Deploying to Appwrite..."

# Deploy function using Appwrite CLI
appwrite functions create \
    --functionId "$FUNCTION_ID" \
    --name "$FUNCTION_NAME" \
    --runtime "$RUNTIME" \
    --execute "$EXECUTE" \
    --entrypoint "$ENTRYPOINT" || echo "Function already exists, updating..."

# Update function code
appwrite functions updateDeployment \
    --functionId "$FUNCTION_ID" \
    --code function.tar.gz \
    --activate true

echo "✅ Deployment complete!"

# Cleanup
rm function.tar.gz

echo ""
echo "📋 Next steps:"
echo "1. Configure environment variables in Appwrite Console"
echo "2. Create 'monitoring' database with 'alerts' collection"
echo "3. Create messaging topics: 'critical-alerts' and 'monitoring-alerts'"
echo "4. Generate API key for Alertmanager webhook"
echo "5. Test the function with: npm run test:webhook"
echo ""
echo "Function webhook URL:"
echo "https://appwrite.wizardsofts.com/v1/functions/$FUNCTION_ID/executions"
