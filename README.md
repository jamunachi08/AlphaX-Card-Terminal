# AlphaX Card Terminal (Driver Framework)

Vendor‑neutral Frappe/ERPNext app to integrate **any** card terminal / payment provider using a **Driver Catalog** model (similar to installing printer drivers in Windows).

This repository is intentionally designed to support multiple integration patterns:

1. **SYNC** drivers (ERP gets immediate approval/decline)
   - Generic REST Gateway
   - Network TCP (stub/protocol-specific)

2. **ASYNC_CALLBACK** drivers (ERP starts capture and waits for agent callback/webhook)
   - MQTT Async Bridge (device/agent subscribes; agent calls ERP callback)
   - Android Mada Agent (MQTT + callback) pattern

3. **CLIENT_SDK** drivers (POS/Desk performs capture using a vendor JS SDK)
   - Stripe Terminal (client SDK pattern)

---

## Core Concepts

### 1) Driver Catalog (Global)
DocType: **AlphaX Terminal Driver**

- A global list of available “drivers” shipped with the app.
- Each record includes:
  - `driver_code`
  - `handler_path` (Python class)
  - `capabilities`
  - `config_schema` (JSON) describing required config fields

This is how the app stays **open for everyone** (not bound to one vendor).

### 2) Terminal Profile (Per Company / Branch)
DocType: **AlphaX Payment Terminal Settings**

- A configuration profile for a specific company/branch/terminal setup.
- Choose a **Driver** and provide **config_json**.
- Link the profile to **Mode of Payment** (MoP) via custom fields shipped as fixtures.

### 3) Session Correlation (Vendor Neutral)
DocType: **AlphaX Terminal Session**

- A universal object to correlate:
  - the payment request (amount, reference),
  - the driver request payload,
  - and the final response/callback.

For async patterns, the session UUID is the anchor.

---

## Included Drivers

Shipped via fixtures (DocType: AlphaX Terminal Driver):

- `simulator` – Demo/testing
- `generic_rest` – REST gateway (SYNC)
- `local_bridge` – Localhost bridge (SYNC/agent‑style stub)
- `network_tcp` – TCP stub (protocol-specific)
- `mqtt_async_bridge` – MQTT async (ASYNC_CALLBACK)
- `android_mada_mqtt` – Android Mada agent async (ASYNC_CALLBACK)
- `stripe_terminal_sdk` – Stripe Terminal client SDK (CLIENT_SDK)

---

## Installation

```bash
bench get-app <repo-url>
bench --site <site> install-app alphax_card_terminal
bench migrate
bench clear-cache
```

---

## Configuration

### 1) Create a Terminal Profile
Open **AlphaX Payment Terminal Settings**:
- Enabled = ON
- Company = your company
- Driver = choose from **AlphaX Terminal Driver**
- Config JSON = according to driver schema

### 2) Bind to Mode of Payment
Open **Mode of Payment**:
- Capture Terminal Data = ON
- Terminal Settings = select the profile
- Require Terminal Approval = ON (optional enforcement)

---

## Runtime APIs

### Driver catalog
- `alphax_card_terminal.api.get_available_drivers()`

### Sessions
- `alphax_card_terminal.api.create_terminal_session(...)`
- `alphax_card_terminal.api.terminal_capture_start(..., session=...)`
- `alphax_card_terminal.api.get_terminal_session_status(uuid)`

### Async callback endpoint
- `POST /api/method/alphax_card_terminal.api.terminal_callback?uuid=<uuid>`

If `callback_secret` is configured in Terminal Settings config_json, send:
- Header: `X-AlphaX-Signature: sha256=<hex>`
- Signature = HMAC-SHA256(body, callback_secret)

---

## Production Hardening Checklist

- Use callback signatures (HMAC) for all async agents.
- Do not store PAN; only masked PAN/last4 if required.
- Enforce “Require Terminal Approval” at **before_submit** (Sales Invoice/POS) for card MoPs.
- Add idempotency (uuid/idempotency_key) to prevent double capture.
- Implement a reconciliation report (ERP payments vs terminal approvals).

