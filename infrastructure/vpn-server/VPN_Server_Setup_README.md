# WireGuard VPN Server Setup (Ubuntu)

This guide documents the complete setup of a WireGuard VPN server on an Ubuntu machine, including key generation, configuration, firewall rules, and adding multiple clients.

---

## ✅ Server Overview

- **VPN Software**: WireGuard
- **OS**: Ubuntu (multi-purpose machine)
- **Network Interface**: `wlp3s0`
- **VPN Subnet**: `10.8.0.0/24`
- **Public IP**: Dynamic with Route53 DDNS (`vpn.wizardsofts.com`)
- **Port Forwarded**: UDP 51820

---

## 📁 Directory Structure

```
/etc/wireguard/
├── wg0.conf              # Main server config
├── keys/                 # Secure key storage (600 permissions)
│   ├── server_private.key
│   ├── server_public.key
│   ├── client1_private.key
│   ├── client1_public.key
│   ├── mashfiq_private.key
│   └── mashfiq_public.key
├── peers/                # Per-client config files
│   ├── client1.conf
│   └── mashfiq.conf
```

---

## 🔐 Key Generation

```
sudo -i
wg genkey | tee /etc/wireguard/keys/<username>_private.key | wg pubkey > /etc/wireguard/keys/<username>_public.key
chmod 600 /etc/wireguard/keys/<username>_*.key
chown root:root /etc/wireguard/keys/<username>_*.key
exit
```

---

## 🧾 Server Config (`wg0.conf`)

```
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = <server_private_key>
PostUp = sysctl -w net.ipv4.ip_forward=1
PostUp = iptables -t nat -A POSTROUTING -o wlp3s0 -j MASQUERADE
PostDown = iptables -t nat -D POSTROUTING -o wlp3s0 -j MASQUERADE

[Peer]
PublicKey = HCe/SuLd4lLcSz7oWoMYf2Xg7T+kPsRUL8G1hp07ok8=
AllowedIPs = 10.8.0.2/32

[Peer]
PublicKey = kdepJCqAhWRQBycGhJyWN9gXHvREwO6dZwSuF8+41Bo=
AllowedIPs = 10.8.0.3/32
```

---

## 🔥 UFW Firewall Rules

```bash
sudo ufw allow 51820/udp
# Edit /etc/ufw/before.rules — add at top:
*nat
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -s 10.8.0.0/24 -o wlp3s0 -j MASQUERADE
COMMIT

# Edit /etc/default/ufw
DEFAULT_FORWARD_POLICY="ACCEPT"

# Reload firewall
sudo ufw disable && sudo ufw enable
```

---

## 🔄 Enable IP Forwarding

```bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo nano /etc/sysctl.conf
# Add:
net.ipv4.ip_forward=1
sudo sysctl -p
```

---

## 🔁 Enable WireGuard on Boot

```bash
sudo systemctl enable wg-quick@wg0
```

---

## 💻 Client Config Template (`<username>.conf`)

```
[Interface]
PrivateKey = <client_private_key>
Address = 10.8.0.X/24
DNS = 1.1.1.1

[Peer]
PublicKey = <server_public_key>
Endpoint = vpn.wizardsofts.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

---

## 🧪 Test & Monitoring

- On server: `sudo wg`
- On client: Use WireGuard app to import `.conf` or scan QR code
- Test with: [https://ifconfig.me](https://ifconfig.me)

---

## 🧠 Notes

- Do **not** use `SaveConfig = true` unless absolutely necessary — it overwrites your manual config.
- Use readable config filenames like `mashfiq.conf`, `alice.conf` for clarity.
- Always secure private keys and backup configs.

---

## 🔐 Active Clients

| Username | VPN IP       | Public Key                                |
|----------|--------------|--------------------------------------------|
| client1  | 10.8.0.2/32  | HCe/SuLd4lLcSz7oWoMYf2Xg7T+kPsRUL8G1hp07ok8= |
| mashfiq  | 10.8.0.3/32  | kdepJCqAhWRQBycGhJyWN9gXHvREwO6dZwSuF8+41Bo= |