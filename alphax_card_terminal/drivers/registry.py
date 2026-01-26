from __future__ import annotations
import importlib
from typing import Any

import frappe

DEFAULT_DRIVER_MAP = {
    "Generic REST": "generic_rest",
    "Local Bridge (localhost)": "local_bridge",
    "Network TCP": "network_tcp",
}

def _load_class(handler_path: str):
    mod_name, cls_name = handler_path.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)

def get_driver(settings_doc):
    """Return a driver instance for a given AlphaX Payment Terminal Settings doc."""
    # Preferred: Link field to AlphaX Terminal Driver
    driver_name = getattr(settings_doc, "driver", None)
    if driver_name:
        rec = frappe.get_doc("AlphaX Terminal Driver", driver_name)
        handler_path = rec.handler_path
        cls = _load_class(handler_path)
        return cls(settings_doc)

    # Backward compatibility: provider select
    provider = getattr(settings_doc, "provider", None)
    code = DEFAULT_DRIVER_MAP.get(provider or "", "simulator")
    # Use built-in default handlers
    handler_path = {
        "generic_rest": "alphax_card_terminal.drivers.impl.generic_rest.GenericRestDriver",
        "local_bridge": "alphax_card_terminal.drivers.impl.local_bridge.LocalBridgeDriver",
        "network_tcp": "alphax_card_terminal.drivers.impl.network_tcp.NetworkTcpDriver",
        "simulator": "alphax_card_terminal.drivers.impl.simulator.SimulatorDriver",
    }[code]
    cls = _load_class(handler_path)
    return cls(settings_doc)
