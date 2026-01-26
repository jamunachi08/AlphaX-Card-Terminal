from __future__ import annotations

from typing import Any, Dict

import frappe

from alphax_card_terminal.drivers.base import BaseTerminalDriver, CaptureRequest, DriverMode


class MqttAsyncBridgeDriver(BaseTerminalDriver):
    """MQTT async driver pattern.

    This driver represents the common KSA pattern:
    ERP publishes a request to an MQTT topic (device/agent subscribes),
    and the device/agent posts results back via HTTP callback/webhook.

    This implementation is intentionally vendor-neutral; protocol specifics live in the agent.
    """

    driver_code = "mqtt_async_bridge"
    driver_name = "MQTT Async Bridge (Agent + Callback)"
    mode = DriverMode.ASYNC_CALLBACK

    def start_capture(self, req: CaptureRequest) -> Dict[str, Any]:
        cfg = self._get_config()

        # The actual MQTT publish requires an MQTT library and broker credentials.
        # We keep it optional: if paho-mqtt exists, you can enable native publish.
        payload = {
            "uuid": req.idempotency_key or frappe.generate_hash(length=24),
            "amount": req.amount,
            "currency": req.currency or cfg.get("currency") or "SAR",
            "mode_of_payment": req.mode_of_payment,
            "reference_doctype": req.reference_doctype,
            "reference_name": req.reference_name,
            "callback_url": cfg.get("callback_url"),
            "merchant_id": cfg.get("merchant_id"),
            "terminal_id": cfg.get("terminal_id"),
        }

        # If configured to publish from ERP, attempt it; otherwise return the payload for an external publisher.
        publish_from_erp = int(cfg.get("publish_from_erp") or 0) == 1
        if publish_from_erp:
            try:
                import paho.mqtt.client as mqtt  # type: ignore
            except Exception:
                return {
                    "status": "ERROR",
                    "message": "MQTT publish requested but paho-mqtt is not installed. Install dependency or set publish_from_erp=0.",
                    "payload": payload,
                }

            broker_host = cfg.get("broker_host")
            broker_port = int(cfg.get("broker_port") or 1883)
            topic = cfg.get("topic")
            if not broker_host or not topic:
                return {"status": "ERROR", "message": "Missing broker_host/topic in config_json.", "payload": payload}

            client = mqtt.Client()
            if cfg.get("username"):
                client.username_pw_set(cfg.get("username"), cfg.get("password"))
            if int(cfg.get("use_ssl") or 0) == 1:
                client.tls_set()  # relies on system defaults; production should pin CA certs if required
            client.connect(broker_host, broker_port, int(cfg.get("keepalive") or 60))
            client.loop_start()
            client.publish(topic, frappe.as_json(payload), qos=int(cfg.get("qos") or 1))
            client.loop_stop()
            client.disconnect()

        return {
            "status": "PENDING",
            "transport": "MQTT",
            "payload": payload,
            "message": "Request prepared. Await device callback to complete.",
        }
