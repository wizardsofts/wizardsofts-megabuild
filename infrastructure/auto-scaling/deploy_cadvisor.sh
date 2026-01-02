#!/bin/bash
# Deploy cAdvisor to all servers for container metrics

echo "Deploying cAdvisor to all servers..."

# Server details
SERVERS=("10.0.0.80" "10.0.0.81" "10.0.0.82" "10.0.0.84")
USERS=("wizardsofts" "wizardsofts" "deploy" "wizardsofts")
PORTS=("22" "22" "2025" "22")

# Loop through each server
for i in "${!SERVERS[@]}"; do
    SERVER=${SERVERS[$i]}
    USER=${USERS[$i]}
    PORT=${PORTS[$i]}
    
    echo "Deploying cAdvisor to $SERVER (User: $USER, Port: $PORT)..."
    
    # Deploy cAdvisor container
    ssh -p $PORT $USER@$SERVER << 'EOF'
        # Check if cAdvisor is already running
        if docker ps | grep -q cadvisor; then
            echo "cAdvisor already running on $HOSTNAME, stopping it..."
            docker stop cadvisor
            docker rm cadvisor
        fi
        
        # Run cAdvisor container
        docker run -d \
          --name=cadvisor \
          --restart=unless-stopped \
          --volume=/:/rootfs:ro \
          --volume=/var/run:/var/run:ro \
          --volume=/sys:/sys:ro \
          --volume=/var/lib/docker/:/var/lib/docker:ro \
          --volume=/dev/disk/:/dev/disk:ro \
          --publish=8080:8080 \
          --privileged \
          --device=/dev/kmsg \
          gcr.io/cadvisor/cadvisor:latest
          
        if [ $? -eq 0 ]; then
            echo "cAdvisor deployed successfully on $HOSTNAME"
        else
            echo "Failed to deploy cAdvisor on $HOSTNAME"
        fi
EOF
    
    if [ $? -eq 0 ]; then
        echo "✓ cAdvisor deployment initiated on $SERVER"
    else
        echo "✗ Failed to deploy cAdvisor on $SERVER"
    fi
    
    echo
done

echo "cAdvisor deployment complete!"
echo "Access metrics at:"
for server in "${SERVERS[@]}"; do
    echo "  - http://$server:8080/metrics"
done