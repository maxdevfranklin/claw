"""Node status reporting to the TrajectoryRL web dashboard.

Sends POST /api/nodes/report with sr25519-signed payloads so the
dashboard can track online nodes.
"""

import logging
import time
from typing import Any, Dict, Optional

import httpx

from trajectoryrl import __version__

logger = logging.getLogger(__name__)

DEFAULT_REPORT_URL = "https://trajrl.com/api/nodes/report"


async def report_status(
    wallet,
    node_type: str,
    uptime: int,
    *,
    status: str = "online",
    report_url: str = DEFAULT_REPORT_URL,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Report node status to the dashboard API.

    Args:
        wallet: bt.Wallet with accessible hotkey for signing.
        node_type: ``"miner"`` or ``"validator"``.
        uptime: Node uptime in seconds.
        status: Current status string (default ``"online"``).
        report_url: Dashboard report endpoint.
        metadata: Arbitrary key-value metadata to attach.

    Returns:
        True on successful report (HTTP 200), False otherwise.
    """
    hotkey_kp = wallet.hotkey
    hotkey_addr = hotkey_kp.ss58_address
    timestamp = int(time.time())

    message = f"trajectoryrl-report:{hotkey_addr}:{timestamp}"
    sig = hotkey_kp.sign(message.encode())
    signature = "0x" + (sig if isinstance(sig, bytes) else bytes(sig)).hex()

    payload: Dict[str, Any] = {
        "hotkey": hotkey_addr,
        "nodeType": node_type,
        "version": __version__,
        "status": status,
        "uptime": uptime,
        "timestamp": timestamp,
        "signature": signature,
    }
    if metadata:
        payload["metadata"] = metadata

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(report_url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.debug("Status reported (hotkey=%s...)", hotkey_addr[:8])
            return True
        logger.warning(
            "Status report failed: %d %s", resp.status_code, resp.text[:200]
        )
        return False
    except Exception as e:
        logger.warning("Status report error: %s", e)
        return False
