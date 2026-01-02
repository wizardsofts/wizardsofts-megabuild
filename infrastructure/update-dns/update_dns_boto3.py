#!/usr/bin/env python3

import os
import json
import logging
import requests
import boto3
# from dotenv import load_dotenv # Not available on server
from dotenv import load_dotenv
from pathlib import Path
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "update_dns.log")),
        logging.StreamHandler()
    ]
)

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables
# Priority: .env in current dir, then home dir config
ENV_FILES = [
    BASE_DIR / ".env",
    Path.home() / "aws_dns.env"
]

for env_file in ENV_FILES:
    if env_file.exists():
        load_dotenv(env_file)
        # Keep loading? Usually first match suffices, but let's load what we find
        # break 

# Config
CONFIG_FILE = BASE_DIR / "domains_config.json"
RECORD_FILE = BASE_DIR / ".last_public_ip.txt"

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=10).text.strip()
    except requests.RequestException as e:
        logging.error(f"Failed to get public IP: {e}")
        exit(1)

def get_last_ip():
    if RECORD_FILE.exists():
        return RECORD_FILE.read_text().strip()
    return ""

def save_current_ip(ip):
    try:
        RECORD_FILE.write_text(ip)
    except IOError as e:
        logging.error(f"Failed to save current IP: {e}")

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load domain config: {e}")
        exit(1)

def update_dns(current_ip):
    domain_configs = load_config()
    start_ip = get_last_ip()

    if current_ip == start_ip:
        logging.info(f"IP {current_ip} has not changed. No update needed.")
        return

    logging.info(f"IP changed from {start_ip} to {current_ip}. Updating records...")

    client = boto3.client("route53")
    
    # Group domains by HostedZoneId
    zone_updates = defaultdict(list)
    for entry in domain_configs:
        zone_updates[entry["hosted_zone_id"]].append(entry["domain"])

    for zone_id, domains in zone_updates.items():
        changes = []
        for domain in domains:
            changes.append({
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": domain,
                    "Type": "A",
                    "TTL": 300,
                    "ResourceRecords": [{"Value": current_ip}]
                }
            })
        
        if not changes:
            continue

        try:
            response = client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    "Comment": f"Auto-update for {', '.join(domains)}",
                    "Changes": changes
                }
            )
            logging.info(f"Updated zone {zone_id} for domains {domains}: Change ID {response['ChangeInfo']['Id']}")
        except Exception as e:
            logging.error(f"Failed to update zone {zone_id}: {e}")

    save_current_ip(current_ip)

if __name__ == "__main__":
    current_ip = get_public_ip()
    update_dns(current_ip)
