"""GSR Automation - Slack-based IP Whitelisting Helper

This script is intended to run **inside** the Google Cloud VM as the first
operational step, before the DLT pipeline touches any external databases.

Responsibilities
----------------
1. Determine the VM's public IPv4 address (metadata service or explicit input).
2. Post a whitelisting command to a Slack channel using a Bot User OAuth token.
3. Provide clear logging and non‑zero exit codes on failure.

Configuration (environment variables)
-------------------------------------
Required:
    SLACK_BOT_TOKEN              # Bot User OAuth Token (xoxb-...)
    SLACK_WHITELIST_CHANNEL      # Channel ID or name (e.g. C0123..., or #alerts)

Optional:
    SLACK_WHITELIST_COMMAND_TEMPLATE  # e.g. "!whitelist-ip {ip}"
    GSR_VM_PUBLIC_IP                  # Override IP instead of using metadata

CLI overrides (all optional):
    --channel / --ip / --command-template / --dry-run

Usage examples (on the VM)
--------------------------
    # Using only environment variables
    python -m slack_whitelist_ip

    # Explicit channel and custom command template
    python slack_whitelist_ip.py \
        --channel C0123ABCDEF \
        --command-template "!whitelist-ip {ip} env=prod"
"""

from __future__ import annotations

import argparse
import ipaddress
import logging
import os
from typing import Optional

import requests

from dotenv import load_dotenv

# Load .env if present (keeps behavior consistent with other project scripts)
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


SLACK_API_URL = "https://slack.com/api/chat.postMessage"
SLACK_BOT_TOKEN_ENV = "SLACK_BOT_TOKEN"
SLACK_CHANNEL_ENV = "SLACK_WHITELIST_CHANNEL"
SLACK_TEMPLATE_ENV = "SLACK_WHITELIST_COMMAND_TEMPLATE"
VM_PUBLIC_IP_ENV = "GSR_VM_PUBLIC_IP"

METADATA_IP_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/"
    "network-interfaces/0/access-configs/0/external-ip"
)
METADATA_HEADERS = {"Metadata-Flavor": "Google"}


def validate_ipv4(ip: str) -> str:
    """Return the IP if it's a valid IPv4 address, else raise ValueError."""

    try:
        addr = ipaddress.ip_address(ip)
    except ValueError as exc:  # includes IPv6 or malformed
        raise ValueError(f"Invalid IP address: {ip}") from exc

    if addr.version != 4:
        raise ValueError(f"Expected IPv4 address, got IPv{addr.version}: {ip}")
    return ip


def get_ip_from_metadata(timeout: float = 2.0) -> str:
    """Retrieve the VM's public IPv4 address from GCE metadata service."""

    logger.info("Attempting to retrieve public IP from GCE metadata service...")
    try:
        resp = requests.get(
            METADATA_IP_URL, headers=METADATA_HEADERS, timeout=timeout
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to query metadata server: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(
            f"Metadata server returned {resp.status_code}: {resp.text!r}"
        )

    ip = resp.text.strip()
    if not ip:
        raise RuntimeError("Metadata server returned an empty IP address")

    logger.info("Public IP from metadata: %s", ip)
    return validate_ipv4(ip)


def resolve_public_ip(explicit_ip: Optional[str] = None) -> str:
    """Resolve the public IPv4 to use.

    Precedence:
        1. CLI argument --ip
        2. Environment variable GSR_VM_PUBLIC_IP
        3. GCE metadata service
    """

    if explicit_ip:
        logger.info("Using IP provided via CLI: %s", explicit_ip)
        return validate_ipv4(explicit_ip)

    env_ip = os.getenv(VM_PUBLIC_IP_ENV)
    if env_ip:
        logger.info("Using IP from %s environment variable: %s", VM_PUBLIC_IP_ENV, env_ip)
        return validate_ipv4(env_ip)

    return get_ip_from_metadata()


def build_whitelist_message(ip: str, template: Optional[str]) -> str:
    """Render the Slack message text using the provided template.

    The template should contain "{ip}" where the IP address should be injected.
    If template is None, a conservative default is used.
    """

    if not template:
        template = "!whitelist-ip {ip}"

    if "{ip}" not in template:
        logger.warning(
            "Whitelist command template does not contain '{ip}'. "
            "Appending IP at the end."
        )
        return f"{template} {ip}"

    return template.format(ip=ip)


def send_slack_message(
    token: str,
    channel: str,
    text: str,
    dry_run: bool = False,
) -> None:
    """Send a message to Slack using chat.postMessage.

    Raises RuntimeError on failure.
    """

    if dry_run:
        logger.info("[DRY RUN] Would post to Slack channel %s: %s", channel, text)
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {"channel": channel, "text": text}

    logger.info("Posting whitelist command to Slack channel %s...", channel)
    try:
        resp = requests.post(SLACK_API_URL, headers=headers, json=payload, timeout=10)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call Slack API: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(
            f"Slack API HTTP {resp.status_code}: {resp.text!r}"
        )

    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error: {data.get('error', 'unknown_error')}")

    logger.info("Slack message sent successfully (ts=%s)", data.get("ts"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Post a whitelisting command to Slack for this VM's public IPv4 address."
        )
    )
    parser.add_argument(
        "--ip",
        help=(
            "Explicit public IPv4 to whitelist. If omitted, uses "
            f"{VM_PUBLIC_IP_ENV} or the GCE metadata service."
        ),
    )
    parser.add_argument(
        "--channel",
        help=(
            "Slack channel ID or name (e.g. C0123..., or #alerts). "
            f"Defaults to {SLACK_CHANNEL_ENV}."
        ),
    )
    parser.add_argument(
        "--command-template",
        help=(
            "Whitelist command template with {ip} placeholder. "
            f"Defaults to {SLACK_TEMPLATE_ENV} or '!whitelist-ip {{ip}}'."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be sent to Slack without actually sending it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    token = os.getenv(SLACK_BOT_TOKEN_ENV)
    if not token:
        logger.error(
            "Slack bot token not configured. Set %s in your environment.",
            SLACK_BOT_TOKEN_ENV,
        )
        return 1

    channel = args.channel or os.getenv(SLACK_CHANNEL_ENV)
    if not channel:
        logger.error(
            "Slack channel not specified. Use --channel or set %s.",
            SLACK_CHANNEL_ENV,
        )
        return 1

    template = args.command_template or os.getenv(SLACK_TEMPLATE_ENV)

    try:
        ip = resolve_public_ip(args.ip)
        message = build_whitelist_message(ip, template)
        logger.info("Final whitelist message: %s", message)
        send_slack_message(token, channel, message, dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001 - top-level guard
        logger.error("Failed to send whitelist request: %s", exc)
        return 1

    logger.info("Whitelist request completed successfully.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

