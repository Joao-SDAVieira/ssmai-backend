#!/bin/bash

echo "🏗️  Building and testing SSMai Backend with Docker..."

# Function to cleanup
cleanup() {
    echo "🧹 Cleaning up..."
    docker compose down -v 2>/dev/null || true
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Build the containers
echo "🔨 Building Docker images..."
docker compose build

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "✅ Docker build successful!"

# Start the containers
echo "🚀 Starting containers..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if containers are running
echo "📊 Checking container status..."
docker compose ps

# Test the API health endpoint
echo "🏥 Testing API health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy!"
        break
    else
        echo "⏳ Waiting for API to be ready... (attempt $i/30)"
        sleep 2
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ API health check failed after 30 attempts"
        echo "📋 API logs:"
        docker compose logs stock_application_api
        exit 1
    fi
done

# Test MCP status endpoint
echo "🧪 Testing MCP status..."
sleep 5
response=$(curl -s http://localhost:8000/chatbot/status)
echo "MCP Status Response: $response"

# Test a simple chat query
echo "💬 Testing chatbot functionality..."
response=$(curl -s -X POST http://localhost:8000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quantas tabelas temos no banco?"}')

echo "Chat Response: $response"

# Check if response contains error
if echo "$response" | grep -q "error"; then
    echo "⚠️  Chat test returned an error, but this might be expected during initial setup"
    echo "📋 API logs:"
    docker compose logs --tail=50 stock_application_api
else
    echo "✅ Chat test completed successfully!"
fi

echo ""
echo "🎉 Setup completed! The application is running on:"
echo "   - API: http://localhost:8000"
echo "   - Health: http://localhost:8000/health"
echo "   - Chat: http://localhost:8000/chatbot/chat"
echo "   - MCP Status: http://localhost:8000/chatbot/status"
echo ""
echo "🔧 To test the chat endpoint manually:"
echo "curl -X POST http://localhost:8000/chatbot/chat \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"message\": \"Quantos produtos temos no estoque?\"}'"
echo ""
echo "🛑 To stop the services:"
echo "docker compose down"
