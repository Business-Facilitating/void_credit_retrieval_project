# Slack-based IP Whitelisting for GCP Deployment

## Overview

The GSR Automation pipeline includes an automated IP whitelisting step that runs as **Step 0** (the first operational step) in the deployment pipeline. This step is essential for allowing the ephemeral Google Cloud VM to access external databases (ClickHouse and PeerDB) before the DLT pipeline executes.

## How It Works

1. **VM Creation**: Google Cloud creates an ephemeral VM with a new public IPv4 address
2. **IP Detection**: The `slack_whitelist_ip.py` script retrieves the VM's public IP from the GCP metadata service
3. **Slack Notification**: The script posts a whitelisting command to a designated Slack channel
4. **Automated Whitelisting**: A bot or integration in the Slack channel processes the command and whitelists the IP
5. **Pipeline Execution**: Once whitelisted, the DLT pipeline can access the databases

## Configuration

### Environment Variables

Add the following variables to your `.env` file:

```bash
# Slack API Configuration (for IP whitelisting in GCP deployment)
SLACK_BOT_TOKEN=xoxb-1196297734070-9958913172178-qwmmXiyCUlZllamu2D2J41bN
SLACK_WHITELIST_CHANNEL=C03B931H51A
SLACK_WHITELIST_COMMAND_TEMPLATE=@G-bot ip_whitelist {ip}
```

#### Required Variables

- **`SLACK_BOT_TOKEN`**: Bot User OAuth Token (starts with `xoxb-`)

  - Obtain from: Slack App Settings → OAuth & Permissions → Bot User OAuth Token
  - Required scopes: `chat:write`, `chat:write.public`

- **`SLACK_WHITELIST_CHANNEL`**: Slack channel where whitelisting commands are posted
  - Current value: `C03B931H51A` (channel where G-bot is present)
  - Format: Channel ID (e.g., `C0123ABCDEF`) or channel name (e.g., `#database-whitelist`)
  - The bot must be added to this channel

#### Optional Variables

- **`SLACK_WHITELIST_COMMAND_TEMPLATE`**: Custom command format

  - Current value: `@G-bot ip_whitelist {ip}` (mentions G-bot and uses ip_whitelist command)
  - Must include `{ip}` placeholder where the IP address will be inserted
  - The `{ip}` placeholder will be replaced with the actual VM IP at runtime
  - Example result: `@G-bot ip_whitelist 203.0.113.42`
  - Other examples:
    - `!whitelist {ip}`
    - `whitelist add {ip} env=production`
    - `/db-whitelist {ip} ttl=24h`

- **`GSR_VM_PUBLIC_IP`**: Override IP address (for testing)
  - If set, uses this IP instead of querying the GCP metadata service

## Google Secret Manager Setup

For GCP deployment, the `.env` file is stored in Google Secret Manager. Make sure to update the secret with the Slack configuration:

```bash
# Update the secret with your .env file
gcloud secrets versions add gsr-automation-env --data-file=.env
```

## Usage

### Automatic Execution (Recommended)

The IP whitelisting step runs automatically as part of the full pipeline:

```bash
make pipeline-full
```

This executes all 5 steps in order:

- **Step 0**: Whitelist VM IP via Slack ← NEW
- **Step 1**: Extract carrier invoice data from ClickHouse
- **Step 2**: Extract industry index logins from PeerDB
- **Step 3**: Filter label-only tracking numbers
- **Step 4**: Automated UPS shipment void

### Manual Execution

To run only the IP whitelisting step:

```bash
# Using Make
make pipeline-step0

# Or directly with Python
poetry run python src/src/slack_whitelist_ip.py
```

### Testing

Test the IP whitelisting without running the full pipeline:

```bash
make test-step0
```

### Dry Run Mode

Test the script without actually sending the Slack message:

```bash
poetry run python src/src/slack_whitelist_ip.py --dry-run
```

### CLI Overrides

Override configuration via command-line arguments:

```bash
# Custom channel
poetry run python src/src/slack_whitelist_ip.py --channel C0123ABCDEF

# Custom IP address (for testing)
poetry run python src/src/slack_whitelist_ip.py --ip 203.0.113.42

# Custom command template
poetry run python src/src/slack_whitelist_ip.py --command-template "!whitelist {ip} env=prod"
```

## Deployment Integration

### Ephemeral VM Deployment (Option 2)

The IP whitelisting step is automatically included in the ephemeral VM deployment:

1. Cloud Scheduler triggers the Cloud Function
2. Cloud Function creates a new VM with a startup script
3. Startup script runs `make pipeline-full`
4. **Step 0** whitelists the VM's IP via Slack
5. Steps 1-4 execute the data pipeline
6. VM self-terminates after completion

### Persistent VM Deployment (Option 1)

For persistent VMs with cron jobs, the IP whitelisting step runs each time the pipeline executes:

```bash
# Crontab entry (runs every other day at 2 AM)
0 2 */2 * * cd /home/user/gsr_automation && make pipeline-full >> logs/cron.log 2>&1
```

## Troubleshooting

### Error: "Slack bot token not configured"

**Solution**: Set `SLACK_BOT_TOKEN` in your `.env` file

### Error: "Slack channel not specified"

**Solution**: Set `SLACK_WHITELIST_CHANNEL` in your `.env` file or use `--channel` CLI argument

### Error: "Failed to query metadata server"

**Cause**: Script is not running on a Google Cloud VM

**Solution**: Use `--ip` CLI argument or set `GSR_VM_PUBLIC_IP` environment variable for local testing

### Error: "Slack API error: not_in_channel"

**Cause**: The bot has not been added to the specified channel

**Solution**:

1. Go to the Slack channel
2. Type `/invite @YourBotName`
3. Or add the bot via channel settings

### Error: "Invalid IP address"

**Cause**: The IP retrieved from metadata or provided manually is not a valid IPv4 address

**Solution**: Verify the IP format (e.g., `203.0.113.42`)

## Security Considerations

1. **Token Security**: The `SLACK_BOT_TOKEN` is sensitive. Store it securely in:

   - `.env` file (never commit to Git)
   - Google Secret Manager (for GCP deployment)
   - Environment variables (for local testing)

2. **Bot Permissions**: Grant minimal required scopes:

   - `chat:write` - Post messages to channels
   - `chat:write.public` - Post to public channels without joining

3. **Channel Access**: Restrict the whitelisting channel to authorized personnel only

4. **IP Validation**: The script validates that the IP is a valid IPv4 address before sending

## Next Steps

1. **Configure Slack Channel**: Provide the channel ID or name
2. **Configure Command Template**: Provide the exact whitelisting command format
3. **Update `.env` file**: Add the Slack configuration
4. **Update Secret Manager**: Upload the updated `.env` to GCP
5. **Test Locally**: Run `make test-step0` to verify the configuration
6. **Deploy**: The IP whitelisting will run automatically in the pipeline

## Related Documentation

- [Google Cloud Deployment Guide](GOOGLE_CLOUD_DEPLOYMENT.md)
- [Deployment Comparison](../deployment/DEPLOYMENT_COMPARISON.md)
- [Security Setup](SECURITY_SETUP.md)
