#!/bin/bash
# deploy_dns.sh

SERVER="wizardsofts@10.0.0.84"
REMOTE_DIR="/home/wizardsofts/scripts/update_dns"
# We don't rely on global env file anymore, will check local .env
# ENV_FILE="/home/deploy/.envs/aws_dns.env" 

# Deploy using existing ControlPath
SSH_OPTS="-o ControlPath=/tmp/deploy_socket"

echo "Deploying to $SERVER at $REMOTE_DIR..."

# Create directory
ssh $SSH_OPTS $SERVER "mkdir -p $REMOTE_DIR"

# Copy files
scp $SSH_OPTS update_dns_boto3.py domains_config.json .env $SERVER:$REMOTE_DIR/

# Setup venv and install requirements
ssh $SSH_OPTS $SERVER "cd $REMOTE_DIR && \
    if [ ! -d 'venv' ]; then \
        python3 -m venv venv; \
    fi && \
    ./venv/bin/pip install requests boto3 python-dotenv"

# Setup Cron (idempotent-ish)
ssh $SSH_OPTS $SERVER "crontab -l | grep -v 'update_dns_boto3.py' | { cat; echo '*/5 * * * * $REMOTE_DIR/venv/bin/python $REMOTE_DIR/update_dns_boto3.py >> $REMOTE_DIR/cron.log 2>&1'; } | crontab -"

echo "Deployment complete."
