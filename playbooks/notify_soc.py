"""
Playbook automation – Notify SOC action.

Simulates sending notifications to the SOC team via email, Slack,
PagerDuty, or ticketing systems. In production, integrates with
real notification channels.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.utils.helpers import get_logger

logger = get_logger(__name__)

PLAYBOOK_NAME = "notify_soc"
PLAYBOOK_DESCRIPTION = "Send alert notification to the SOC team"


def execute(
    target: str,                        # IP or hostname that triggered the alert
    alert_id: str,
    alert_type: str = "Security Alert",
    severity: str = "High",
    reason: Optional[str] = None,
    executed_by: str = "system",
) -> Dict[str, Any]:
    """
    Execute the Notify SOC playbook.

    Sends a structured notification to SOC channels.
    In production: integrates with email SMTP, Slack webhooks, PagerDuty.

    Parameters
    ----------
    target       : Affected IP or host.
    alert_id     : Alert identifier.
    alert_type   : Type of security alert.
    severity     : Alert severity level.
    reason       : Notification reason/context.
    executed_by  : Triggering user or "system".

    Returns
    -------
    dict : Notification delivery result.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    notification_id = f"NOTIF-{abs(hash(alert_id + timestamp)) % 99999:05d}"

    logger.info(
        "PLAYBOOK [notify_soc] | alert=%s type=%s severity=%s by=%s",
        alert_id, alert_type, severity, executed_by,
    )

    message = (
        f"🚨 SOAR Alert Notification\n"
        f"Alert ID: {alert_id}\n"
        f"Type: {alert_type}\n"
        f"Severity: {severity}\n"
        f"Target: {target}\n"
        f"Time: {timestamp}\n"
        f"Reason: {reason or 'Automated SOC notification'}\n"
        f"Triggered by: {executed_by}"
    )

    result = {
        "playbook":        PLAYBOOK_NAME,
        "action":          "SOC_NOTIFIED",
        "target":          target,
        "alert_id":        alert_id,
        "notification_id": notification_id,
        "reason":          reason or "Automated SOC notification",
        "executed_by":     executed_by,
        "executed_at":     timestamp,
        "status":          "Success",
        "message":         f"SOC notified successfully. Notification ID: {notification_id}",
        "simulated":       True,
        "channels_notified": [
            "Email: soc-team@company.com",
            "Slack: #security-alerts",
            "PagerDuty: SOC On-call",
        ],
        "notification_body": message,
    }

    logger.info(
        "PLAYBOOK [notify_soc] SUCCESS | alert=%s notification_id=%s",
        alert_id, notification_id,
    )
    return result
