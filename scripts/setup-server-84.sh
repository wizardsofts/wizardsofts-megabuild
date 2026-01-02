#!/bin/bash
# Server Setup Script for 10.0.0.84
# Automates GitLab Runner and Docker setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration (use environment variables for secrets)
SUDO_PASSWORD="${SUDO_PASSWORD:?Error: SUDO_PASSWORD environment variable must be set}"
DEPLOY_PATH="/opt/wizardsofts-megabuild"
DEPLOY_USER="deploy"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Wizardsofts Megabuild Server Setup${NC}"
echo -e "${GREEN}Server: 10.0.0.84${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to run commands with sudo
run_sudo() {
    echo "$SUDO_PASSWORD" | sudo -S "$@"
}

# 1. Update system
echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
run_sudo apt-get update
run_sudo apt-get upgrade -y

# 2. Install required packages
echo -e "${YELLOW}Step 2: Installing required packages...${NC}"
run_sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    rsync \
    sshpass \
    build-essential

# 3. Install Docker
echo -e "${YELLOW}Step 3: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    run_sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | run_sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Set up Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | run_sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    run_sudo apt-get update
    run_sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add current user to docker group
    run_sudo usermod -aG docker $USER

    # Start Docker service
    run_sudo systemctl enable docker
    run_sudo systemctl start docker

    echo -e "${GREEN}✓ Docker installed successfully${NC}"
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi

docker --version
docker compose version

# 4. Install GitLab Runner
echo -e "${YELLOW}Step 4: Installing GitLab Runner...${NC}"
if ! command -v gitlab-runner &> /dev/null; then
    # Download GitLab Runner binary
    run_sudo curl -L --output /usr/local/bin/gitlab-runner https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64

    # Give execute permissions
    run_sudo chmod +x /usr/local/bin/gitlab-runner

    # Create GitLab Runner user
    run_sudo useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash || echo "User already exists"

    # Install and run as service
    run_sudo gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
    run_sudo gitlab-runner start

    # Add gitlab-runner to docker group
    run_sudo usermod -aG docker gitlab-runner

    echo -e "${GREEN}✓ GitLab Runner installed successfully${NC}"
else
    echo -e "${GREEN}✓ GitLab Runner already installed${NC}"
fi

gitlab-runner --version

# 5. Create deployment directory
echo -e "${YELLOW}Step 5: Creating deployment directory...${NC}"
run_sudo mkdir -p $DEPLOY_PATH
run_sudo chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH
echo -e "${GREEN}✓ Deployment directory created at $DEPLOY_PATH${NC}"

# 6. Configure firewall (optional)
echo -e "${YELLOW}Step 6: Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    run_sudo ufw allow 22/tcp     # SSH
    run_sudo ufw allow 80/tcp     # HTTP
    run_sudo ufw allow 443/tcp    # HTTPS
    run_sudo ufw allow 3001/tcp   # Frontend
    run_sudo ufw allow 8080/tcp   # Gateway
    run_sudo ufw allow 8761/tcp   # Eureka
    echo -e "${GREEN}✓ Firewall rules configured${NC}"
else
    echo -e "${YELLOW}⚠ UFW not installed, skipping firewall configuration${NC}"
fi

# 7. Create systemd service for auto-start (optional)
echo -e "${YELLOW}Step 7: Creating systemd service...${NC}"
cat <<EOF | run_sudo tee /etc/systemd/system/wizardsofts-megabuild.service
[Unit]
Description=Wizardsofts Megabuild Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DEPLOY_PATH
ExecStart=/usr/bin/docker compose --profile gibd-quant up -d
ExecStop=/usr/bin/docker compose --profile gibd-quant down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

run_sudo systemctl daemon-reload
echo -e "${GREEN}✓ Systemd service created${NC}"

# 8. Display next steps
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Register GitLab Runner:"
echo "   sudo gitlab-runner register"
echo "   - URL: https://gitlab.com/"
echo "   - Token: [Get from GitLab Settings → CI/CD → Runners]"
echo "   - Executor: docker"
echo "   - Default image: alpine:latest"
echo ""
echo "2. Configure Runner for Docker-in-Docker:"
echo "   sudo nano /etc/gitlab-runner/config.toml"
echo "   - Set: privileged = true"
echo "   - Set: volumes = [\"/var/run/docker.sock:/var/run/docker.sock\", \"/cache\"]"
echo "   sudo gitlab-runner restart"
echo ""
echo "3. Clone repository to deployment directory:"
echo "   cd $DEPLOY_PATH"
echo "   git clone https://gitlab.com/your-username/wizardsofts-megabuild.git ."
echo ""
echo "4. Create .env file:"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "5. Build and start services:"
echo "   docker compose --profile gibd-quant up -d"
echo ""
echo "6. Enable auto-start on boot (optional):"
echo "   sudo systemctl enable wizardsofts-megabuild"
echo ""
echo -e "${GREEN}Server is ready for deployment!${NC}"
echo ""
echo "For detailed instructions, see:"
echo "  docs/GITLAB_RUNNER_SETUP.md"
echo ""
