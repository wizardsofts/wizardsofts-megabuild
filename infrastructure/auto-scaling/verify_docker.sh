#!/bin/bash
# Docker verification script for auto-scaling platform
# Run this script on your control server to verify Docker installation on all servers

echo "=== Docker Verification for Auto-Scaling Platform ==="
echo "Checking Docker installation on all 4 servers..."
echo

# Define server details
SERVERS=("10.0.0.80" "10.0.0.81" "10.0.0.82" "10.0.0.84")
USERS=("wizardsofts" "wizardsofts" "deploy" "wizardsofts")
PORTS=("22" "22" "2025" "22")

# Create results directory
mkdir -p verification_results
DATE=$(date +%Y%m%d_%H%M%S)

# Loop through each server
for i in "${!SERVERS[@]}"; do
    SERVER=${SERVERS[$i]}
    USER=${USERS[$i]}
    PORT=${PORTS[$i]}
    
    echo "Checking server $SERVER (User: $USER, Port: $PORT)..."
    
    # Test SSH connectivity first
    if ssh -p $PORT -o ConnectTimeout=10 -o StrictHostKeyChecking=no $USER@$SERVER "echo connected" >/dev/null 2>&1; then
        echo "  ✓ SSH connection successful"
        
        # Check Docker version
        DOCKER_VERSION=$(ssh -p $PORT -o StrictHostKeyChecking=no $USER@$SERVER "docker --version" 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "  ✓ Docker installed: $DOCKER_VERSION"
            
            # Check if Docker daemon is running
            DOCKER_STATUS=$(ssh -p $PORT -o StrictHostKeyChecking=no $USER@$SERVER "systemctl is-active docker" 2>/dev/null)
            if [ "$DOCKER_STATUS" = "active" ]; then
                echo "  ✓ Docker service is running"
            else
                echo "  ⚠ Docker service is not running"
            fi
            
            # Test basic Docker functionality
            DOCKER_TEST=$(ssh -p $PORT -o StrictHostKeyChecking=no $USER@$SERVER "docker run --rm hello-world" 2>&1 | grep "Hello from Docker" | wc -l)
            if [ $DOCKER_TEST -gt 0 ]; then
                echo "  ✓ Docker functionality test passed"
            else
                echo "  ⚠ Docker functionality test failed"
            fi
        else
            echo "  ✗ Docker not installed"
        fi
    else
        echo "  ✗ SSH connection failed to $SERVER"
    fi
    echo
done

echo "Verification complete. Results saved to verification_results/docker_verification_$DATE.txt"