"""
Playbook automation – Isolate Host action.

Simulates isolating a compromised endpoint from the network.
In production, integrates with EDR platforms (CrowdStrike Falcon,
Microsoft Defender, Carbon Black) or NAC solutions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.utils.helpers import get_logger

logger = get_logger(__name__)

PLAYBOOK_NAME = "isolate_host"
PLAYBOOK_DESCRIPTION = "Isolate a compromised host from the network"


def execute(
    target: str,                     # hostname or IP of the host
    alert_id: str,
    reason: Optional[str] = None,
    executed_by: str = "system",
) -> Dict[str, Any]:
    """
    Execute the Isolate Host playbook.

    In production: calls EDR API to quarantine the endpoint.

    Parameters
    ----------
    target       : Hostname or IP address of the host to isolate.
    alert_id     : Originating alert ID.
    reason       : Human-readable isolation reason.
    executed_by  : Username or "system".

    Returns
    -------
    dict : Execution result.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    ticket_id = f"ISOLATE-{abs(hash(target + alert_id)) % 99999:05d}"

    logger.info(
        "PLAYBOOK [isolate_host] | target=%s alert=%s by=%s",
        target, alert_id, executed_by,
    )

    result = {
        "playbook":      PLAYBOOK_NAME,
        "action":        "HOST_ISOLATED",
        "target":        target,
        "alert_id":      alert_id,
        "ticket_id":     ticket_id,
        "reason":        reason or "Automated isolation via SOAR playbook",
        "executed_by":   executed_by,
        "executed_at":   timestamp,
        "status":        "Success",
        "message":       f"Host '{target}' successfully isolated. Ticket: {ticket_id}",
        "simulated":     True,
        "actions_taken": [
            f"EDR isolation command sent to agent on {target}",
            f"Network VLAN changed: Quarantine VLAN activated",
            f"DNS blocked for host {target}",
            f"Active sessions terminated for {target}",
        ],
    }

    logger.info(
        "PLAYBOOK [isolate_host] SUCCESS | target=%s ticket=%s",
        target, ticket_id,
    )
    return result
