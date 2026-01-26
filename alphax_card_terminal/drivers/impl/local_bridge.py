from __future__ import annotations
from typing import Any, Dict

import frappe
from alphax_card_terminal.drivers.base import BaseTerminalDriver, CaptureRequest

class LocalBridgeDriver(BaseTerminalDriver):
    driver_code = "local_bridge"
    driver_name = "Local Bridge (localhost)"

    def start_capture(self, req: CaptureRequest) -> Dict[str, Any]:
        cfg = self._get_config()
        url = cfg.get("endpoint_url") or "http://127.0.0.1:9797/capture"
        payload = {
            "amount": req.amount,
            "currency": req.currency,
            "reference_doctype": req.reference_doctype,
            "reference_name": req.reference_name,
            "mode_of_payment": req.mode_of_payment,
        }
        try:
            resp = frappe.make_post_request(url, data=payload, timeout=cfg.get("timeout_seconds") or 60)
            return resp if isinstance(resp, dict) else {"status":"Error","message":"Invalid response from bridge.","raw":resp}
        except Exception as e:
            return {"status":"Error","message":str(e)}

    def test_connection(self) -> Dict[str, Any]:
        cfg = self._get_config()
        url = (cfg.get("endpoint_url") or "http://127.0.0.1:9797").rstrip("/")
        try:
            resp = frappe.make_get_request(url + "/ping", timeout=10)
            return {"ok": True, "message": "Bridge reachable", "raw": resp}
        except Exception as e:
            return {"ok": False, "message": str(e)}
