#!/bin/bash
# Setup wizardsofts user on Server 82 with passwordless sudo
# Run this script on Server 82 as root/admin user

set -e

USERNAME="wizardsofts"
USER_HOME="/home/${USERNAME}"

echo "=== Setting up ${USERNAME} user on Server 82 ==="

# Step 1: Check if user exists, create if not
if id "$USERNAME" &>/dev/null; then
    echo "[1/5] User $USERNAME already exists"
else
    echo "[1/5] Creating user $USERNAME..."
    useradd -m -s /bin/bash "$USERNAME"
    echo "User created"
fi

# Step 2: Setup passwordless sudo
echo "[2/5] Configuring passwordless sudo..."
if ! grep -q "^${USERNAME} ALL=(ALL) NOPASSWD:ALL" /etc/sudoers.d/${USERNAME} 2>/dev/null; then
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME}
    chmod 0440 /etc/sudoers.d/${USERNAME}
    echo "Passwordless sudo configured"
else
    echo "Passwordless sudo already configured"
fi

# Step 3: Add to docker group
echo "[3/5] Adding user to docker group..."
if ! groups "$USERNAME" | grep -q docker; then
    usermod -aG docker "$USERNAME"
    echo "Added to docker group"
else
    echo "Already in docker group"
fi

# Step 4: Setup SSH directory and authorized_keys
echo "[4/5] Setting up SSH keys..."
mkdir -p "${USER_HOME}/.ssh"

# Copy authorized_keys from Server 80 if not exists
if [ ! -f "${USER_HOME}/.ssh/authorized_keys" ]; then
    echo "Fetching SSH keys from Server 80..."
    scp wizardsofts@10.0.0.80:~/.ssh/authorized_keys "${USER_HOME}/.ssh/authorized_keys" 2>/dev/null || {
        echo "WARNING: Could not copy keys from Server 80"
        echo "You'll need to manually add SSH keys later"
        touch "${USER_HOME}/.ssh/authorized_keys"
    }
fi

chmod 700 "${USER_HOME}/.ssh"
chmod 600 "${USER_HOME}/.ssh/authorized_keys"
chown -R "${USERNAME}:${USERNAME}" "${USER_HOME}/.ssh"
echo "SSH keys configured"

# Step 5: Verify setup
echo "[5/5] Verifying setup..."

# Check sudo
if sudo -u "$USERNAME" sudo -n true 2>/dev/null; then
    echo "✅ Passwordless sudo: OK"
else
    echo "❌ Passwordless sudo: FAILED"
fi

# Check docker
if sudo -u "$USERNAME" docker ps >/dev/null 2>&1; then
    echo "✅ Docker access: OK"
else
    echo "⚠️  Docker access: User needs to logout/login for group to take effect"
fi

# Check SSH
if [ -f "${USER_HOME}/.ssh/authorized_keys" ] && [ -s "${USER_HOME}/.ssh/authorized_keys" ]; then
    echo "✅ SSH keys: OK ($(wc -l < ${USER_HOME}/.ssh/authorized_keys) keys)"
else
    echo "⚠️  SSH keys: Empty or missing"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Test with:"
echo "  ssh wizardsofts@10.0.0.82 'sudo whoami'"
echo "  ssh wizardsofts@10.0.0.82 'docker ps'"
echo "  ssh wizardsofts@10.0.0.82 'free -h'"
echo ""
