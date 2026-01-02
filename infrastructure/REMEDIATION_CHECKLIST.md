# Server Security Remediation Checklist
## Target: 10.0.0.84 (GMK NucBox) | Date: December 19, 2025

---

## 📋 PRE-REMEDIATION CHECKLIST

- [ ] Read and understand the vulnerability report
- [ ] Review all identified vulnerabilities  
- [ ] Ensure SSH password is available in `.env` files
- [ ] Have backup plan in case remediation causes issues
- [ ] Schedule remediation during maintenance window
- [ ] Notify stakeholders of security updates

---

## 🚀 REMEDIATION EXECUTION CHECKLIST

### Phase 1: Environment Setup

- [ ] Navigate to workspace directory:
  ```bash
  cd /Users/mashfiqurrahman/Workspace/wizardsofts/server-setup
  ```

- [ ] Load environment variables:
  ```bash
  source .env && source hardening/.env
  ```

- [ ] Verify variables are loaded:
  ```bash
  echo "Target: $TARGET_IP | User: $TARGET_USER"
  ```

### Phase 2: Quick Remediation (Optional - if time is limited)

- [ ] Run quick remediation script:
  ```bash
  bash hardening/scripts/quick_remediate.sh "$TARGET_IP" "$TARGET_USER" "$SSH_PASSWORD"
  ```

- [ ] Verify script completed without errors
- [ ] Check server is still accessible via SSH

### Phase 3: Comprehensive Hardening (Recommended)

- [ ] Run full hardening framework:
  ```bash
  bash hardening/harden.sh "$TARGET_IP" "$TARGET_USER" apply
  ```

- [ ] Monitor progress in terminal
- [ ] Wait for "Hardening complete" message
- [ ] Note any errors or warnings

### Phase 4: Post-Hardening Verification

- [ ] Verify SSH still works:
  ```bash
  ssh $TARGET_USER@$TARGET_IP "echo 'SSH works'"
  ```

- [ ] Check hardening status:
  ```bash
  bash hardening/scripts/06_security_tools.sh "$TARGET_IP" "$TARGET_USER" check
  ```

- [ ] Review hardening logs:
  ```bash
  tail -100 hardening/logs/*apply*.log
  ```

### Phase 5: Re-scan for Vulnerabilities

- [ ] Run vulnerability scan again:
  ```bash
  bash hardening/scripts/scan_vulnerabilities.sh "$TARGET_IP" "$TARGET_USER"
  ```

- [ ] Review new scan report:
  ```bash
  cat hardening/logs/vulnerability_scans/*latest*.log
  ```

- [ ] Verify critical vulnerabilities are fixed
- [ ] Document any remaining issues

---

## ✅ POST-REMEDIATION VERIFICATION

### Critical Vulnerabilities (Should be Fixed)

- [ ] System updates applied (33 packages updated)
- [ ] Telnet and FTP removed
- [ ] Auditd installed and running
- [ ] SSH configuration hardened
- [ ] SSH config permissions corrected (600)
- [ ] IP forwarding disabled
- [ ] /root permissions set to 700

### High Priority (Should be Verified)

- [ ] Firewall (UFW) is active
- [ ] Fail2Ban is installed and running
- [ ] Audit rules configured
- [ ] IPv6 reviewed (disabled if not needed)
- [ ] Docker user group membership reviewed

### Positive Indicators

- [ ] Server SSH connectivity working
- [ ] No critical errors in logs
- [ ] Hardening completed successfully
- [ ] All services restarted properly

---

## 📊 VULNERABILITY CLOSURE TRACKING

### Critical Issues

| Issue | Status | Evidence |
|-------|--------|----------|
| System updates pending | ⬜ Pending | Check: `apt list --upgradable` |
| Telnet/FTP installed | ⬜ Pending | Check: `dpkg -l \| grep -E "telnet\|ftp"` |
| Auditd not installed | ⬜ Pending | Check: `sudo systemctl status auditd` |
| SSH not hardened | ⬜ Pending | Check: `sudo grep "^PermitRootLogin" /etc/ssh/sshd_config` |

### High Priority Issues  

| Issue | Status | Evidence |
|-------|--------|----------|
| SSH config permissions | ⬜ Pending | Check: `stat -c '%a' /etc/ssh/sshd_config` |
| IP forwarding enabled | ⬜ Pending | Check: `cat /proc/sys/net/ipv4/ip_forward` |
| IPv6 enabled | ⬜ Pending | Check: `cat /proc/sys/net/ipv6/conf/all/disable_ipv6` |
| Docker user privileges | ⬜ Pending | Check: `groups` |

---

## 🔧 MANUAL VERIFICATION COMMANDS

If automated scripts don't work, verify manually:

```bash
# SSH to server
ssh $TARGET_USER@$TARGET_IP

# Check system updates
sudo apt list --upgradable | wc -l

# Check for risky packages
dpkg -l | grep -E "telnet|ftp"

# Check auditd status
sudo systemctl status auditd

# Check SSH hardening
sudo grep "^PermitRootLogin\|^PasswordAuthentication\|^PubkeyAuthentication" /etc/ssh/sshd_config

# Check file permissions
stat -c '%a' /etc/ssh/sshd_config
stat -c '%a' /root

# Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward

# Check firewall
sudo ufw status

# Check fail2ban
sudo systemctl status fail2ban

# Check audit logs
sudo tail -20 /var/log/audit/audit.log
```

---

## 📁 LOG FILES LOCATION

All remediation logs are saved to:
```
hardening/logs/
├── 10.0.0.84_*.log           # Main hardening logs
├── VULNERABILITY_REPORT_*.md  # Detailed vulnerability report
└── vulnerability_scans/
    └── 10.0.0.84_vulnerability_scan_*.log  # Raw scan output
```

View latest log:
```bash
ls -lt hardening/logs/ | head -5
tail -200 hardening/logs/10.0.0.84_*.log
```

---

## 🚨 ROLLBACK PROCEDURE

If something goes wrong:

```bash
# 1. Check if rollback scripts exist
ls hardening/scripts/*rollback* 2>/dev/null || echo "No rollback scripts found"

# 2. Review what was changed
git diff HEAD hardening/

# 3. If needed, restore from git (if changes were committed)
cd hardening
git restore .  # Restore original state

# 4. Or manually revert specific changes:
# - Re-enable telnet/ftp if needed
# - Disable auditd if needed
# - Restore original SSH config from backup
```

---

## 📞 TROUBLESHOOTING

### If SSH connection fails after hardening:
```bash
# Check SSH service
ssh $TARGET_USER@$TARGET_IP "sudo systemctl status sshd"

# Restart SSH service
ssh $TARGET_USER@$TARGET_IP "sudo systemctl restart sshd"

# Check SSH config for syntax errors
ssh $TARGET_USER@$TARGET_IP "sudo sshd -t"
```

### If hardening script fails:
```bash
# Review error in log
tail -100 hardening/logs/10.0.0.84_*.log | grep -i error

# Re-run specific phase
bash hardening/scripts/06_security_tools.sh "$TARGET_IP" "$TARGET_USER" apply
```

### If permissions are incorrect:
```bash
# SSH to server and fix manually
ssh $TARGET_USER@$TARGET_IP << 'EOF'
sudo chmod 600 /etc/ssh/sshd_config
sudo chmod 700 /root
sudo chmod 640 /etc/shadow
sudo systemctl restart sshd
EOF
```

---

## ✨ SUCCESS CRITERIA

Remediation is successful when:

✅ All critical vulnerabilities are resolved  
✅ High priority issues are addressed  
✅ Server SSH connectivity works  
✅ Hardening logs show no critical errors  
✅ Re-scan shows significant vulnerability reduction  
✅ Auditd is logging  
✅ Fail2Ban is running  
✅ Firewall is active  

---

## 📝 SIGN-OFF

- [ ] Remediation completed successfully
- [ ] All verification checks passed
- [ ] Logs reviewed and archived
- [ ] Stakeholders notified
- [ ] Schedule next security audit (30 days)

**Date Completed:** _______________  
**Completed By:** _______________  
**Server:** 10.0.0.84 (GMK NucBox)  
**Vulnerabilities Resolved:** 13/13

---

## 🎯 NEXT STEPS

1. **Schedule Monthly Scans:**
   ```bash
   # Add to crontab for monthly vulnerability scans
   0 2 1 * * cd /path/to/workspace && bash hardening/scripts/scan_vulnerabilities.sh 10.0.0.84 wizardsofts >> /var/log/vuln_scan.log 2>&1
   ```

2. **Review Audit Logs Weekly:**
   ```bash
   ssh $TARGET_USER@$TARGET_IP "sudo tail -100 /var/log/audit/audit.log"
   ```

3. **Monitor Fail2Ban:**
   ```bash
   ssh $TARGET_USER@$TARGET_IP "sudo tail -20 /var/log/fail2ban.log"
   ```

4. **Keep System Updated:**
   ```bash
   ssh $TARGET_USER@$TARGET_IP "sudo apt update && sudo apt upgrade -y"
   ```

---

**Checklist Version:** 1.0  
**Last Updated:** December 19, 2025  
**Status:** Ready for Use ✓
