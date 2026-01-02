# GMK Server (10.0.0.84) Hardening Plan

## Overview
Comprehensive security hardening plan to restrict external access and enforce strict execution permissions on the GMK server.

---

## Phase 1: Network Access Control

### 1.1 SSH Hardening
- [ ] **Restrict SSH to Local Subnet Only**
  - Add UFW rule: `ufw allow from 10.0.0.0/24 to any port 22`
  - Add UFW rule: `ufw default deny incoming`
  - Verify external IPs cannot connect: `nc -zv <external-ip> 22`

- [ ] **SSH Configuration Hardening** (Edit `/etc/ssh/sshd_config`)
  - Disable root login: `PermitRootLogin no`
  - Disable password authentication: `PasswordAuthentication no`
  - Enable public key authentication: `PubkeyAuthentication yes`
  - Disable empty passwords: `PermitEmptyPasswords no`
  - Set max auth attempts: `MaxAuthAttempts 3`
  - Set login grace time: `LoginGraceTime 20`
  - Disable X11 forwarding: `X11Forwarding no`
  - Disable port forwarding: `AllowTcpForwarding no`
  - Set protocol version 2: `Protocol 2`
  - Use strong key exchange algorithms
  - Disable unused authentication methods

- [ ] **SSH Key Management**
  - Ensure SSH keys have correct permissions: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`
  - Remove weak keys, enforce ed25519 or RSA 4096+
  - Disable root SSH login completely

### 1.2 Firewall Configuration
- [ ] **UFW Rules**
  ```bash
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow from 10.0.0.0/24 to any port 22
  ufw allow from 10.0.0.0/24 to any port 53  # DNS only for local
  ufw enable
  ```

- [ ] **Rate Limiting**
  - Limit SSH connections: `ufw limit 22/tcp`
  - Limit DNS queries: `ufw limit 53/udp`

---

## Phase 2: File System Hardening

### 2.1 Execution Permissions
- [ ] **Restrict World-Executable Files**
  ```bash
  # Find and audit world-executable files
  find / -type f -perm -001 -not -path "/proc/*" -not -path "/sys/*" 2>/dev/null
  # Remove unnecessary world execute permissions
  find /usr/local -type f -perm -001 -exec chmod o-x {} \;
  ```

- [ ] **SUID/SGID Audit and Hardening**
  ```bash
  # Find SUID/SGID binaries
  find / -type f \( -perm -4000 -o -perm -2000 \) -not -path "/proc/*" -not -path "/sys/*" 2>/dev/null
  # Remove unnecessary SUID/SGID: chmod u-s,g-s <file>
  # Keep only essential: sudo, passwd, su, etc.
  ```

- [ ] **Application Directory Permissions**
  ```bash
  # /opt/apps should not be world-writable
  chmod 750 /opt/apps
  chmod 750 /opt/apps/llm-server
  chmod 700 /opt/apps/llm-server/data
  
  # Restrict user home directories
  chmod 700 /home/wizardsofts
  chmod 700 /home/wizardsofts/.ssh
  chmod 600 /home/wizardsofts/.ssh/authorized_keys
  ```

### 2.2 Temporary Directory Hardening
- [ ] **Mount Options for /tmp and /var/tmp**
  - Edit `/etc/fstab` and remount with: `noexec,nosuid,nodev,mode=1777`
  - Verify: `mount | grep tmp`

- [ ] **Disable Unnecessary Directories**
  - Remove unnecessary world-writable directories
  - Audit `/dev/shm` permissions (should be `noexec,nosuid,nodev`)

### 2.3 File Permissions Audit
- [ ] **Sensitive Files**
  ```bash
  chmod 600 /etc/ssh/sshd_config
  chmod 644 /etc/ssh/sshd_config.pub
  chmod 600 /root/.ssh/authorized_keys
  chmod 644 /etc/sudoers  # Should be verified with visudo
  chmod 640 /var/log/auth.log
  chmod 640 /var/log/syslog
  ```

---

## Phase 3: User & Sudo Hardening

### 3.1 User Account Hardening
- [ ] **Disable Unnecessary User Accounts**
  ```bash
  # Identify unused accounts
  lastlog
  # Disable accounts: usermod -L <username>
  ```

- [ ] **Remove Unnecessary Groups**
  - Review `/etc/group` and `/etc/gshadow`
  - Remove unused groups: `groupdel <groupname>`

### 3.2 Sudo Configuration
- [ ] **Restrict Sudo Access**
  - Edit `/etc/sudoers` (use `visudo`):
    - `wizardsofts ALL=(ALL) NOPASSWD: ALL` → `wizardsofts ALL=(ALL) ALL` (require password)
    - Add `Defaults requiretty` (require terminal for sudo)
    - Add `Defaults use_pty` (sudo runs in pseudo-terminal)
    - Add `Defaults log_host, log_command` (audit sudo commands)
    - Add `Defaults ignore_dot` (ignore .env files)

- [ ] **Limit Root Access**
  - `PermitRootLogin no` in sshd_config
  - Ensure root cannot login via SSH

### 3.3 Password Policy
- [ ] **Configure PAM Password Policy**
  - Install: `apt install libpam-pwquality`
  - Configure minimum password requirements in `/etc/security/pwquality.conf`:
    - minlen=14
    - dcredit=-1 (at least 1 digit)
    - ucredit=-1 (at least 1 uppercase)
    - lcredit=-1 (at least 1 lowercase)
    - ocredit=-1 (at least 1 special character)

- [ ] **Set Password Expiration**
  ```bash
  # In /etc/login.defs
  PASS_MAX_DAYS   90
  PASS_MIN_DAYS   1
  PASS_WARN_AGE   7
  ```

---

## Phase 4: Service Hardening

### 4.1 Disable Unnecessary Services
- [ ] **Review and Disable Services**
  ```bash
  # Services that can be disabled:
  systemctl disable bluetooth.service      # If not needed
  systemctl disable cups.service           # Printer service
  systemctl disable avahi-daemon.service   # mDNS
  
  # Stop them:
  systemctl stop <service>
  ```

- [ ] **Mask Unnecessary Services**
  ```bash
  systemctl mask bluetooth.service
  ```

### 4.2 Systemd Service Hardening
- [ ] **Harden SSH Service** - Create `/etc/systemd/system/ssh.service.d/hardening.conf`:
  ```ini
  [Service]
  PrivateTmp=yes
  NoNewPrivileges=yes
  ProtectSystem=strict
  ProtectHome=yes
  ReadWritePaths=/etc/ssh /var/run/sshd
  ProtectKernelTunables=yes
  ProtectControlGroups=yes
  RestrictRealtime=yes
  RestrictNamespaces=yes
  LockPersonality=yes
  MemoryDenyWriteExecute=yes
  RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
  SystemCallFilter=~@clock @debug @module @obsolete @privileged @raw-io @reboot @swap
  ```

### 4.3 Docker Security
- [ ] **Restrict Docker Socket Access**
  - `chmod 660 /var/run/docker.sock`
  - `usermod -aG docker wizardsofts` (Only if necessary)

- [ ] **Docker Rootless Mode (Recommended)**
  - Install dependencies: `apt install dbus-user-session uidmap`
  - Run setup: `dockerd-rootless-setuptool.sh install`
  - This prevents container escapes from gaining root access to the host.

- [ ] **Docker Daemon Hardening** - Edit `/etc/docker/daemon.json`:
  ```json
  {
    "userns-remap": "default",
    "icc": false,
    "no-new-privileges": true,
    "default-ulimits": {
      "nofile": {
        "Name": "nofile",
        "Hard": 2048,
        "Soft": 1024
      }
    },
    "live-restore": true,
    "log-driver": "json-file",
    "log-opts": {
      "max-size": "10m",
      "max-file": "3"
    },
    "storage-driver": "overlay2"
  }
  ```

### 4.4 AppArmor Enforcement
- [ ] **Verify AppArmor Status**
  - `aa-status`
- [ ] **Enforce Profiles**
  - Ensure Docker containers use the default AppArmor profile: `docker-default`
  - Audit and enforce profiles for critical services: `aa-enforce /etc/apparmor.d/*`

---

## Phase 5: Kernel & System Hardening

### 5.1 Kernel Parameters (sysctl)
- [ ] **Create `/etc/sysctl.d/99-hardening.conf`:**
  ```bash
  # IP Forwarding - Disable if not routing traffic
  net.ipv4.ip_forward = 0
  net.ipv6.conf.all.forwarding = 0
  
  # ICMP Settings - Disable ICMP redirect acceptance
  net.ipv4.conf.all.accept_redirects = 0
  net.ipv4.conf.default.accept_redirects = 0
  net.ipv6.conf.all.accept_redirects = 0
  net.ipv6.conf.default.accept_redirects = 0
  
  # Send ICMP Redirects - Disable
  net.ipv4.conf.all.send_redirects = 0
  net.ipv4.conf.default.send_redirects = 0
  
  # SYN Flood Protection
  net.ipv4.tcp_syncookies = 1
  net.ipv4.tcp_syn_retries = 2
  net.ipv4.tcp_synack_retries = 2
  net.ipv4.tcp_max_syn_backlog = 4096
  
  # ICMP Ping - Disable ICMP echo
  net.ipv4.icmp_echo_ignore_all = 0
  net.ipv4.icmp_echo_ignore_broadcasts = 1
  
  # Bad Error Messages - Ignore
  net.ipv4.icmp_ignore_bogus_error_responses = 1
  
  # Reverse Path Filtering
  net.ipv4.conf.all.rp_filter = 1
  net.ipv4.conf.default.rp_filter = 1
  
  # Log Suspicious Packets
  net.ipv4.conf.all.log_martians = 1
  net.ipv4.conf.default.log_martians = 1
  
  # Ignore ICMP Timestamp Requests
  net.ipv4.icmp_timestamps = 0
  
  # Restrict Kernel Pointer Exposure
  kernel.kptr_restrict = 2
  
  # Restrict Kernel Debug Information
  kernel.dmesg_restrict = 1
  
  # Restrict Access to Kernel Memory
  kernel.unprivileged_bpf_disabled = 1
  kernel.unprivileged_userns_clone = 0
  
  # Restrict Performance Event Access
  kernel.perf_event_paranoid = 3
  
  # Restrict ptrace Scope
  kernel.yama.ptrace_scope = 2
  
  # Hide Process Information
  kernel.hidepid = 2
  kernel.hide_kmesg_logs = 1
  
  # Core Dumps - Disable or restrict
  kernel.core_uses_pid = 1
  fs.suid_dumpable = 0
  
  # Magic SysRq Key - Disable
  kernel.sysrq = 0
  
  # Module Loading - Restrict
  kernel.modules_disabled = 1
  
  # Restrict Access to Kernel Logs
  kernel.printk = 3 3 3 3
  ```

- [ ] **Apply Kernel Parameters**
  ```bash
  sysctl -p /etc/sysctl.d/99-hardening.conf
  ```

### 5.2 Disable Unnecessary Kernel Modules
- [ ] **Create `/etc/modprobe.d/hardening.conf`:**
  ```bash
  # Disable uncommon filesystems
  install cramfs /bin/true
  install freevxfs /bin/true
  install jffs2 /bin/true
  install udf /bin/true
  install vfat /bin/true
  
  # Disable uncommon protocols
  install sctp /bin/true
  install rds /bin/true
  install tipc /bin/true
  install dccp /bin/true
  
  # Disable USB storage if not needed
  install usb-storage /bin/true
  ```

---

## Phase 6: Security Tools & Monitoring

### 6.1 Intrusion Detection
- [ ] **Install and Configure Fail2Ban**
  ```bash
  apt install fail2ban
  # Configure /etc/fail2ban/jail.local
  systemctl enable fail2ban
  systemctl start fail2ban
  ```

- [ ] **Create `/etc/fail2ban/jail.local`:**
  ```ini
  [DEFAULT]
  bantime = 3600
  findtime = 600
  maxretry = 3
  destemail = admin@example.com
  sendername = Fail2Ban
  
  [sshd]
  enabled = true
  port = ssh
  filter = sshd
  logpath = /var/log/auth.log
  maxretry = 3
  bantime = 7200
  ```

### 6.2 Audit Framework
- [ ] **Install auditd**
  ```bash
  apt install auditd audispd-plugins
  systemctl enable auditd
  systemctl start auditd
  ```

- [ ] **Configure Audit Rules** - Edit `/etc/audit/rules.d/hardening.rules`:
  ```bash
  # Remove any existing rules
  -D
  
  # Buffer Size
  -b 8192
  
  # Failure Mode - Panic if audit cannot write logs
  -f 2
  
  # Audit sudo usage
  -w /etc/sudoers -p wa -k sudoers
  -w /etc/sudoers.d/ -p wa -k sudoers
  
  # Audit system calls - execve
  -a always,exit -F arch=b64 -S execve -F uid=1000 -k user_commands
  
  # Audit file deletion
  -a always,exit -F arch=b64 -S unlink,unlinkat,rename,renameat -F auid>=1000 -F auid!=4294967295 -k delete
  
  # Audit network configuration
  -w /etc/hosts -p wa -k network_modifications
  -w /etc/hostname -p wa -k network_modifications
  -w /etc/sysconfig/network -p wa -k network_modifications
  
  # Audit SSH configuration
  -w /etc/ssh/sshd_config -p wa -k sshd_config
  
  # Make configuration immutable
  -e 2
  ```

- [ ] **Load and Verify Audit Rules**
  ```bash
  augenrules --load
  auditctl -l  # List rules
  ```

### 6.3 File Integrity Monitoring
- [ ] **Install AIDE (Advanced Intrusion Detection Environment)**
  ```bash
  apt install aide aide-common
  aideinit  # Initialize database
  cp /var/lib/aide/aide.db /var/lib/aide/aide.db.known_good
  ```

- [ ] **Schedule AIDE Checks**
  ```bash
  # Add to crontab
  0 3 * * * /usr/bin/aide --config=/etc/aide/aide.conf --check | mail -s "AIDE Daily Report" root
  ```

### 6.4 Log Monitoring
- [ ] **Configure Log Rotation**
  - Edit `/etc/logrotate.d/syslog`
  - Ensure logs are rotated weekly and kept for 12 weeks minimum

- [ ] **Remote Logging (Centralization)**
  - Configure rsyslog to send logs to a central server (e.g., 10.0.0.80):
    - Edit `/etc/rsyslog.conf`: Add `*.* @10.0.0.80:514`
  - This prevents an attacker from deleting local logs to hide their tracks.

- [ ] **Monitor Failed Login Attempts**
  ```bash
  # Check regularly
  grep "Failed password" /var/log/auth.log
  grep "authentication failure" /var/log/auth.log
  ```

---

## Phase 7: Compliance & Hardening Checklist

### 7.1 CIS Benchmark Compliance
- [ ] Run CIS benchmark check: `apt install lynis && lynis audit system`
- [ ] Address high-priority findings

### 7.2 Firewall Rule Testing
- [ ] From external IP: `ssh -v wizardsofts@10.0.0.84` → Should timeout
- [ ] From local IP (10.0.0.x): `ssh wizardsofts@10.0.0.84` → Should connect
- [ ] Verify port scanning from outside shows no open ports

### 7.3 Permission Verification
- [ ] `find / -perm -001 -type f 2>/dev/null | wc -l` → Should be minimal
- [ ] `find / -perm -4000 -o -perm -2000 2>/dev/null | wc -l` → Review all

### 7.4 Service Audit
- [ ] `systemctl list-units --state=running` → Only necessary services
- [ ] `netstat -tlnp` → Only SSH and DNS listening

---

## Phase 8: Documentation & Testing

### 8.1 Change Documentation
- [ ] Document all changes made
- [ ] Create rollback procedures
- [ ] Test from different network segments

### 8.2 Automated Testing
- [ ] Create script to verify hardening:
  ```bash
  #!/bin/bash
  # Test external connectivity
  echo "Testing SSH from external IP..."
  nc -zv <external-ip> 22
  
  # Test internal connectivity
  echo "Testing SSH from local subnet..."
  nc -zv 10.0.0.80 22  # From another local server
  
  # Verify file permissions
  echo "Checking /opt/apps permissions..."
  ls -ld /opt/apps
  ```

### 8.3 Post-Hardening Audit
- [ ] Run security audit tools:
  - `lynis audit system`
  - `nmap -sV -p- localhost`
  - Manual permission review

---

## Phase 9: Advanced Security & Physical Protection

### 9.1 Physical Security
- [ ] **BIOS/UEFI Password**
  - Set a strong BIOS/UEFI password to prevent unauthorized boot order changes.
- [ ] **Disable USB Boot**
  - Disable booting from USB devices in BIOS/UEFI.
- [ ] **Secure Boot**
  - Ensure Secure Boot is enabled to prevent loading unsigned/malicious kernels.

### 9.2 Kernel Livepatching
- [ ] **Enable Ubuntu Pro (Livepatch)**
  - `pro attach <token>`
  - `pro enable livepatch`
  - This allows applying critical kernel security patches without rebooting.

### 9.3 USB Security (USBGuard)
- [ ] **Install USBGuard**
  - `apt install usbguard`
  - `usbguard generate-policy > /etc/usbguard/rules.conf`
  - `systemctl enable usbguard`
  - This prevents "BadUSB" attacks by blocking unauthorized USB devices.

---

## Estimated Timeline

| Phase | Tasks | Estimated Time |
|-------|-------|-----------------|
| Phase 1 | Network & SSH | 30 min |
| Phase 2 | File Permissions | 45 min |
| Phase 3 | User/Sudo/Password | 30 min |
| Phase 4 | Services & Systemd | 45 min |
| Phase 5 | Kernel Hardening | 30 min |
| Phase 6 | Security Tools | 60 min |
| Phase 7 | Testing & Compliance | 60 min |
| **Total** | | **~5 hours** |

---

## Implementation Notes

### Prerequisites
- Root or sudo access
- Backup of critical configurations
- Test plan in place before changes

### Risk Mitigation
- Make changes incrementally
- Test SSH access before disabling password auth
- Verify firewall rules before enabling
- Keep recovery procedures documented

### Rollback Procedures
- Keep `.bak` copies of all modified files
- Document all changes with timestamps
- Test external connectivity after each phase

---

## Success Criteria

✅ **Network Security:**
- SSH accessible only from 10.0.0.0/24 subnet
- No other services exposed externally
- Firewall actively blocking external connections

✅ **File System:**
- No unnecessary world-executable files
- /tmp, /var/tmp mounted with noexec
- /opt/apps permissions restricted to 750

✅ **Access Control:**
- No password-based SSH authentication
- Root SSH login disabled
- Sudo requires password and logging

✅ **Monitoring:**
- Fail2ban monitoring SSH attempts
- auditd logging suspicious activities
- AIDE detecting file changes

✅ **Compliance:**
- Kernel hardening parameters applied
- Unnecessary services disabled
- Security tools operational
