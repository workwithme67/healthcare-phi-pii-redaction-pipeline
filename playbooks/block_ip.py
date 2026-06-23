"""
Playbook automation files – Block IP action.

This module simulates blocking an IP at the firewall/network level.
In production, this would integrate with firewall APIs, WAF rules,
network ACLs, or SIEM blocking mechanisms.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.utils.helpers import get_logger

logger = get_logger(__name__)

PLAYBOOK_NAME = "block_ip"
PLAYBOOK_DESCRIPTION = "Block a malicious IP address at the network perimeter"


def execute(
    ip_address: str,
    alert_id: str,
    reason: Optional[str] = None,
    executed_by: str = "system",
) -> Dict[str, Any]:
    """
    Execute the Block IP playbook.

    In a real environment this would call firewall/WAF APIs.
    This implementation logs the action and returns a success result.

    Parameters
    ----------
    ip_address   : The IPv4 address to block.
    alert_id     : The originating alert ID for audit purposes.
    reason       : Human-readable reason for the block.
    executed_by  : Username or "system" that triggered this action.

    Returns
    -------
    dict : Execution result with status and details.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(
        "PLAYBOOK [block_ip] | ip=%s alert=%s reason=%r by=%s",
        ip_address, alert_id, reason, executed_by,
    )

    # ── Simulated firewall rule creation ─────────────────────────────────────
    # In production: call firewall API, iptables, Palo Alto PAN-OS, etc.
    simulated_rule_id = f"BLOCK-RULE-{abs(hash(ip_address)) % 99999:05d}"

    result = {
        "playbook":       PLAYBOOK_NAME,
        "action":         "IP_BLOCKED",
        "target":         ip_address,
        "alert_id":       alert_id,
        "rule_id":        simulated_rule_id,
        "reason":         reason or "Automated block via SOAR playbook",
        "executed_by":    executed_by,
        "executed_at":    timestamp,
        "status":         "Success",
        "message":        f"IP {ip_address} successfully blocked. Rule ID: {simulated_rule_id}",
        "simulated":      True,  # Remove in production
        "actions_taken": [
            f"Firewall ACL rule created: DENY {ip_address}",
            f"WAF block rule added: IP={ip_address}",
            f"IDS/IPS signature triggered: {ip_address}",
        ],
    }

    logger.info(
        "PLAYBOOK [block_ip] SUCCESS | ip=%s rule_id=%s",
        ip_address, simulated_rule_id,
    )
    return result
