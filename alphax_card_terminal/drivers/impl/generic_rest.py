from __future__ import annotations
from typing import Any, Dict

import frappe
from alphax_card_terminal.drivers.base import BaseTerminalDriver, CaptureRequest

class GenericRestDriver(BaseTerminalDriver):
    driver_code = "generic_rest"
    driver_name = "Generic REST (HTTP)"

    def start_capture(self, req: CaptureRequest) -> Dict[str, Any]:
        cfg = self._get_config()
        url = cfg.get("endpoint_url")
        if not url:
            return {"status":"Error","message":"endpoint_url is required for Generic REST driver."}
        payload = {
            "amount": req.amount,
            "currency": req.currency,
            "mode_of_payment": req.mode_of_payment,
            "reference_doctype": req.reference_doctype,
            "reference_name": req.reference_name,
            "merchant_id": cfg.get("merchant_id"),
            "terminal_id": cfg.get("terminal_id"),
        }
        try:
            # Frappe helper uses requests internally
            resp = frappe.make_post_request(url, data=payload, timeout=cfg.get("timeout_seconds") or 45)
            # Expect dict response
            if isinstance(resp, dict):
                return resp
            return {"status":"Error","message":"Invalid response type from endpoint.", "raw": resp}
        except Exception as e:
            return {"status":"Error","message":str(e)}

    def test_connection(self) -> Dict[str, Any]:
        cfg = self._get_config()
        url = cfg.get("endpoint_url")
        if not url:
            return {"ok": False, "message": "endpoint_url is required."}
        try:
            resp = frappe.make_post_request(url.rstrip("/") + "/ping", data={}, timeout=10)
            return {"ok": True, "message": "Ping OK", "raw": resp}
        except Exception as e:
            return {"ok": False, "message": str(e)}
