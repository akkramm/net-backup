"""Network config backup tool (Project 1).

Reads devices from inventory/devices.yml, logs in over SSH with Netmiko,
saves 'show running-config' to backups/<device>/<device>_<timestamp>.cfg
and prints a pass/fail summary.

Credentials come from environment variables (.env file), never from code.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

BASE_DIR = Path(__file__).resolve().parent
INVENTORY_FILE = BASE_DIR / "inventory" / "devices.yml"
BACKUP_DIR = BASE_DIR / "backups"

log = logging.getLogger("net-backup")


def load_inventory(path):
    """Return the list of device dicts from the YAML inventory."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["devices"]


def get_credentials():
    """Read login details from the environment. Exit early if missing."""
    username = os.getenv("NET_USERNAME")
    password = os.getenv("NET_PASSWORD")
    secret = os.getenv("NET_SECRET")  # enable password, optional
    if not username or not password:
        sys.exit("NET_USERNAME and NET_PASSWORD must be set (see .env.example)")
    return username, password, secret


def save_backup(name, config):
    """Write the config to backups/<name>/<name>_<timestamp>.cfg."""
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    device_dir = BACKUP_DIR / name
    device_dir.mkdir(parents=True, exist_ok=True)
    out_file = device_dir / f"{name}_{stamp}.cfg"
    out_file.write_text(config, encoding="utf-8")
    return out_file


def backup_device(device, creds):
    """Back up one device. Returns (status, detail)."""
    name = device["name"]
    username, password, secret = creds

    params = {
        "device_type": device.get("device_type", "cisco_ios"),
        "host": device["host"],
        "username": username,
        "password": password,
    }
    if secret:
        params["secret"] = secret

    try:
        log.info("Connecting to %s (%s)", name, device["host"])
        with ConnectHandler(**params) as conn:
            if secret:
                conn.enable()
            config = conn.send_command("show running-config")
        out_file = save_backup(name, config)
        log.info("Saved %s", out_file)
        return "OK", str(out_file.relative_to(BASE_DIR))
    except NetmikoAuthenticationException:
        return "FAILED", "authentication failed"
    except NetmikoTimeoutException:
        return "FAILED", "connection timed out"
    except Exception as exc:  # keep one bad device from stopping the run
        return "FAILED", f"{type(exc).__name__}: {exc}"


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    load_dotenv(BASE_DIR / ".env")
    creds = get_credentials()
    devices = load_inventory(INVENTORY_FILE)

    results = []
    for device in devices:
        status, detail = backup_device(device, creds)
        results.append((device["name"], status, detail))

    print("\nBackup summary")
    print("-" * 60)
    for name, status, detail in results:
        print(f"{name:<12} {status:<8} {detail}")

    failed = sum(1 for _, status, _ in results if status != "OK")
    print("-" * 60)
    print(f"{len(results) - failed} succeeded, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
