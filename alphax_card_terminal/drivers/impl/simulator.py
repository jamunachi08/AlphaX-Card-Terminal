from __future__ import annotations
from typing import Any, Dict

import frappe
from alphax_card_terminal.drivers.base import BaseTerminalDriver, CaptureRequest

class SimulatorDriver(BaseTerminalDriver):
    driver_code = "simulator"
    driver_name = "Simulator (Demo/Training)"

    def start_capture(self, req: CaptureRequest) -> Dict[str, Any]:
        # Deterministic simulation: amounts ending with .99 decline; else approve.
        try:
            amt = float(req.amount)
        except Exception:
            amt = 0.0
        status = "Approved"
        if str(amt).endswith("0.99") or str(amt).endswith(".99"):
            status = "Declined"
        return {
            "status": status,
            "amount": req.amount,
            "currency": req.currency,
            "mode_of_payment": req.mode_of_payment,
            "reference_doctype": req.reference_doctype,
            "reference_name": req.reference_name,
            "rrn": frappe.generate_hash(length=12).upper(),
            "auth_code": frappe.generate_hash(length=6).upper(),
            "response_code": "00" if status == "Approved" else "05",
            "response_message": "SIMULATED APPROVAL" if status == "Approved" else "SIMULATED DECLINE",
            "terminal_id": getattr(self.settings, "terminal_id", None),
            "merchant_id": getattr(self.settings, "merchant_id", None),
            "raw": {"simulator": True},
        }

    def test_connection(self) -> Dict[str, Any]:
        return {"ok": True, "message": "Simulator ready."}
