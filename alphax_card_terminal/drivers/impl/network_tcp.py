from __future__ import annotations
from typing import Any, Dict

from alphax_card_terminal.drivers.base import BaseTerminalDriver, CaptureRequest

class NetworkTcpDriver(BaseTerminalDriver):
    driver_code = "network_tcp"
    driver_name = "Network TCP (LAN Terminal)"

    def start_capture(self, req: CaptureRequest) -> Dict[str, Any]:
        cfg = self._get_config()
        ip = cfg.get("terminal_ip")
        port = cfg.get("terminal_port")
        if not ip or not port:
            return {"status":"Error","message":"terminal_ip and terminal_port are required for Network TCP driver."}
        # Stub: implement vendor protocol in customer-specific driver
        return {
            "status":"PENDING",
            "message":"Network TCP driver stub. Implement protocol for your terminal vendor.",
            "terminal_ip": ip,
            "terminal_port": port,
            "amount": req.amount,
            "currency": req.currency,
        }

    def test_connection(self) -> Dict[str, Any]:
        cfg = self._get_config()
        ip = cfg.get("terminal_ip")
        port = cfg.get("terminal_port")
        if not ip or not port:
            return {"ok": False, "message": "terminal_ip and terminal_port are required."}
        return {"ok": True, "message": "Configuration looks valid (connectivity test not implemented)."}
