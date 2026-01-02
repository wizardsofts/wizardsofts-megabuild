# Dynamic DNS Updater for AWS Route 53

This Python script automatically updates the **A records** of multiple domains in AWS Route 53 based on the current **public IP address** of the host machine. It's useful for maintaining DNS records on a home or dynamic IP server.

---

## ✅ Features

- Supports multiple domain updates using a JSON config file
- Avoids unnecessary updates by checking last known IP
- Uses AWS SDK (`boto3`) to interact with Route 53
- Securely loads credentials using `python-dotenv`

---

## 📁 Project Structure

```
/opt/scripts/update_dns/
├── update_dns_boto3.py            # Main script
├── .last_public_ip.txt            # Stores last known public IP
├── domains_config.json            # Configuration file with domain/zone info
└── venv/                          # Python virtual environment (optional)
```

---

## 🔧 Requirements

- Python 3.7+
- AWS credentials configured via `~/.aws/credentials` or environment variables
- `boto3`, `requests`, `python-dotenv`

You can install dependencies using:

```bash
pip install boto3 requests python-dotenv
```

---

## 🛠 Setup

### 1. Clone the repository or copy the script to your server

### 2. Create `.env` file (optional)

If you're using environment variables:

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=your-region
```

Save this as `/home/deploy/.envs/aws_dns.env`.

### 3. Create `domains_config.json`

Example:
```json
[
  {
    "domain": "api.dailydeenguide.com.",
    "hosted_zone_id": "Z05973601H6LWFYYAF1V8"
  },
  {
    "domain": "www.dailydeenguide.com.",
    "hosted_zone_id": "Z05973601H6LWFYYAF1V8"
  }
]
```

Make sure to **include the trailing dot** in the domain names.

---

## 🚀 Usage

Run the script manually:

```bash
sudo /opt/scripts/update_dns/update_dns_boto3.py
```

Or set it as a cron job:

```bash
*/10 * * * * /opt/scripts/update_dns/update_dns_boto3.py >> /var/log/update_dns.log 2>&1
```

---

## 📓 Notes

- The script will only update records if the public IP has changed.
- Uses [ipify.org](https://www.ipify.org) to get the current IP.
- You can modify the TTL or record type if needed.

---

## 🛡 Security Tip

Ensure only the root or deploy user has access to the `.env` and config files.

```bash
chmod 600 /home/deploy/.envs/aws_dns.env
chmod 600 /opt/scripts/update_dns/domains_config.json
```

---