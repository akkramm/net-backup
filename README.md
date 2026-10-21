# net-backup

A small Python tool that backs up the running configuration of network devices over SSH.

It reads a device list from a YAML inventory, connects with Netmiko, saves each
device's `show running-config` to a timestamped file, and prints a summary of
which devices succeeded or failed.

Tested in an EVE-NG lab with Cisco IOS routers and switches.

## Project layout

```
net-backup/
├── backup.py              # main script
├── inventory/devices.yml  # list of devices
├── backups/               # output (ignored by git)
├── requirements.txt
├── .env.example           # template for credentials
└── .gitignore
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt

copy .env.example .env         # Windows (use cp on Linux / macOS)
# edit .env with your lab username and password
# edit inventory/devices.yml with your EVE-NG device IPs
```

## Run

```bash
python backup.py
```

Backups are saved as `backups/<device>/<device>_<date>_<time>.cfg`.

## Security notes

- Credentials are read from environment variables, never hard-coded.
- `.env` and `backups/` are git-ignored because configs can contain secrets.

## Roadmap

- [ ] Concurrent backups with threads
- [ ] Skip saving when the config has not changed
- [ ] Per-device credentials / Ansible-vault style secret handling
- [ ] Automatic git commit of config changes with a diff report
