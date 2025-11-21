# Slack IP Whitelisting - Quick Reference

## 🎯 Purpose

Automatically whitelist the GCP VM's public IP address before the DLT pipeline runs, enabling database access to ClickHouse and PeerDB.

---

## ⚙️ Configuration (.env)

```bash
SLACK_BOT_TOKEN=xoxb-1196297734070-9958913172178-qwmmXiyCUlZllamu2D2J41bN
SLACK_WHITELIST_CHANNEL=C03B931H51A
SLACK_WHITELIST_COMMAND_TEMPLATE=@G-bot ip_whitelist {ip}
```

---

## 🚀 Quick Commands

```bash
# Test IP whitelisting (dry run)
poetry run python src/src/slack_whitelist_ip.py --dry-run

# Test IP whitelisting (actual Slack message)
make test-step0

# Run full pipeline (includes IP whitelisting as Step 0)
make pipeline-full

# Run only IP whitelisting step
make pipeline-step0
```

---

## 🔧 CLI Overrides

```bash
# Custom channel
poetry run python src/src/slack_whitelist_ip.py --channel C0123ABCDEF

# Custom IP (for testing)
poetry run python src/src/slack_whitelist_ip.py --ip 203.0.113.42

# Custom command template
poetry run python src/src/slack_whitelist_ip.py --command-template "!whitelist {ip} env=prod"

# Dry run (no actual Slack message)
poetry run python src/src/slack_whitelist_ip.py --dry-run
```

---

## 📊 Pipeline Order

```
Step 0: 🔐 Whitelist VM IP via Slack (NEW)
  ↓ (wait 10 seconds)
Step 1: 🚀 Extract from ClickHouse
  ↓ (wait 60 seconds)
Step 2: 📊 Extract from PeerDB
  ↓ (wait 60 seconds)
Step 3: 🔍 Filter tracking numbers
  ↓ (wait 120 seconds)
Step 4: 🌐 UPS void automation
```

---

## 🐛 Common Issues

| Error                             | Solution                                |
| --------------------------------- | --------------------------------------- |
| "Slack bot token not configured"  | Set `SLACK_BOT_TOKEN` in `.env`         |
| "Slack channel not specified"     | Set `SLACK_WHITELIST_CHANNEL` in `.env` |
| "Failed to query metadata server" | Use `--ip` flag for local testing       |
| "Slack API error: not_in_channel" | Add bot to channel: `/invite @BotName`  |
| "Invalid IP address"              | Verify IP format (e.g., `203.0.113.42`) |

---

## 🔐 GCP Secret Manager

```bash
# Update secret with new .env
gcloud secrets versions add gsr-automation-env --data-file=.env

# Verify secret
gcloud secrets versions access latest --secret=gsr-automation-env
```

---

## 📝 How It Works

1. VM starts → Script retrieves public IP from GCP metadata
2. Script posts whitelisting command to Slack channel
3. Slack bot/integration processes command and whitelists IP
4. Pipeline continues with database access enabled

---

## 🔗 Full Documentation

See `docs/SLACK_IP_WHITELISTING.md` for complete details.
