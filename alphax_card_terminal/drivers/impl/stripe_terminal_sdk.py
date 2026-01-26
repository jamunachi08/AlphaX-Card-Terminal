from __future__ import annotations

from typing import Any, Dict

from alphax_card_terminal.drivers.base import BaseTerminalDriver, CaptureRequest, DriverMode


class StripeTerminalSdkDriver(BaseTerminalDriver):
    """Stripe Terminal pattern (client SDK).

    Capture happens in POS/Desk JS using Stripe Terminal SDK.
    Server responsibilities:
    - create connection token
    - create/update/capture/cancel PaymentIntent
    This driver provides the config surface and client hints; full implementation is provided via the POS script layer.

    Note: We intentionally do not bundle stripe-python dependency here. Add it in your deployment image if needed.
    """

    driver_code = "stripe_terminal_sdk"
    driver_name = "Stripe Terminal (Client SDK)"
    mode = DriverMode.CLIENT_SDK

    def start_capture(self, req: CaptureRequest) -> Dict[str, Any]:
        # For client SDK drivers, ERP returns client instructions.
        cfg = self._get_config()
        return {
            "status": "CLIENT_ACTION_REQUIRED",
            "client": {
                "provider": "stripe_terminal",
                "public_key": cfg.get("stripe_public_key"),
                "location_id": cfg.get("stripe_location_id"),
                "currency": (req.currency or cfg.get("currency") or "sar").lower(),
                "amount": req.amount,
                "reference_name": req.reference_name,
            },
            "message": "Capture must be performed in POS/Desk using Stripe Terminal JS SDK. Use API get_stripe_connection_token & create_payment_intent.",
        }

    def get_client_config(self) -> Dict[str, Any]:
        cfg = self._get_config()
        return {
            "provider": "stripe_terminal",
            "public_key": cfg.get("stripe_public_key"),
            "location_id": cfg.get("stripe_location_id"),
        }
