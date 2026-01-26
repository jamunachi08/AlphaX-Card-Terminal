from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import frappe


class DriverMode(str, Enum):
    """How the terminal interaction completes."""
    SYNC = "SYNC"                 # ERP gets final approval/decline in the same call
    ASYNC_CALLBACK = "ASYNC_CALLBACK"  # ERP starts capture, waits for device callback/webhook
    CLIENT_SDK = "CLIENT_SDK"     # Capture happens in client (POS/Desk JS) using vendor SDK


@dataclass
class CaptureRequest:
    mode_of_payment: str
    amount: float
    currency: Optional[str] = None
    reference_doctype: Optional[str] = None
    reference_name: Optional[str] = None
    idempotency_key: Optional[str] = None


class BaseTerminalDriver:
    """Base class for terminal drivers.

    Design goals:
    - Vendor-neutral core (driver catalog + profiles).
    - Extensible drivers (MQTT bridge, Android agent, JS SDK like Stripe Terminal, REST gateways, etc.).
    - Drivers are stateless; all configuration comes from Terminal Settings and/or linked Device docs.
    """

    driver_code: str = "base"
    driver_name: str = "Base Driver"
    mode: DriverMode = DriverMode.SYNC

    def __init__(self, settings_doc):
        self.settings = settings_doc

    # --- Required ---
    def start_capture(self, req: CaptureRequest) -> Dict[str, Any]:
        """Start a capture.

        Return contract (minimum):
        - SYNC: {status: APPROVED|DECLINED|ERROR, response: {...}}
        - ASYNC_CALLBACK: {status: PENDING, uuid: <uuid>, transport: <hint>, request: {...}}
        - CLIENT_SDK: {status: CLIENT_ACTION_REQUIRED, client: {...}}
        """
        raise NotImplementedError

    # --- Optional ---
    def test_connection(self) -> Dict[str, Any]:
        return {"ok": True, "message": "No connection test implemented for this driver."}

    def get_client_config(self) -> Dict[str, Any]:
        """For CLIENT_SDK drivers: returns info the POS UI needs (public keys, locations, etc.)."""
        return {}

    def verify_callback(self, raw_body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """For ASYNC_CALLBACK drivers: validate callback authenticity.
        Return {ok: bool, message?: str}.
        """
        return {"ok": True}

    # --- Helpers ---
    def _get_config(self) -> Dict[str, Any]:
        # Merge explicit fields + config_json (if provided)
        cfg: Dict[str, Any] = {}
        for k in [
            "endpoint_url",
            "terminal_ip",
            "terminal_port",
            "timeout_seconds",
            "merchant_id",
            "terminal_id",
            "provider",
        ]:
            if hasattr(self.settings, k):
                v = getattr(self.settings, k, None)
                if v not in (None, ""):
                    cfg[k] = v

        # config_json overrides
        try:
            if getattr(self.settings, "config_json", None):
                cfg.update(frappe.parse_json(self.settings.config_json))
        except Exception:
            pass
        return cfg
