from __future__ import annotations

from typing import Any, Dict

from alphax_card_terminal.drivers.base import BaseTerminalDriver, CaptureRequest, DriverMode


class AndroidMadaMqttDriver(BaseTerminalDriver):
    """Android Mada Agent over MQTT + HTTP callback.

    Intended for the 'Android bridge' pattern:
    - ERP publishes capture request to topic = device_code (e.g., Android ID)
    - Android agent invokes Mada app via intent
    - Agent POSTs result to callback_url

    This driver is a thin config wrapper around the generic MQTT async bridge.
    """

    driver_code = "android_mada_mqtt"
    driver_name = "Android Mada Agent (MQTT + Callback)"
    mode = DriverMode.ASYNC_CALLBACK

    def start_capture(self, req: CaptureRequest) -> Dict[str, Any]:
        cfg = self._get_config()
        # Normalize keys expected by agents
        payload = {
            "uuid": req.idempotency_key,
            "amount": req.amount,
            "currency": req.currency or cfg.get("currency") or "SAR",
            "invoice_number": req.reference_name,
            "callback_url": cfg.get("callback_url"),
            "device_code": cfg.get("device_code"),
            "topic": cfg.get("topic") or cfg.get("device_code"),
            "merchant_id": cfg.get("merchant_id"),
            "terminal_id": cfg.get("terminal_id"),
            "operation": cfg.get("operation") or "SALE",
        }
        return {
            "status": "PENDING",
            "transport": "MQTT",
            "payload": payload,
            "message": "Android agent should execute Mada and POST callback to ERP.",
        }
