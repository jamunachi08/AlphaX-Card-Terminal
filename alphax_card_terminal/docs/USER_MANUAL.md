# AlphaX Card Terminal (vNext) — User Manual

Version: 0.0.4  
Audience: ERPNext/Frappe Administrators, Implementation Consultants, POS Supervisors, Finance/Audit teams.

---

## 1) What this app does

AlphaX Card Terminal is a **vendor-neutral terminal integration framework** for ERPNext/Frappe.

- It does **not** process card data itself.
- It orchestrates **terminal capture**, stores **non-sensitive metadata**, and enforces **approval rules**.
- It supports multiple integration styles via **Drivers**:
  - Simulator (demo/testing)
  - REST middleware
  - TCP bridge
  - MQTT/Android agent (Aisino A90 / Smart POS)
  - Client SDK (e.g., Stripe Terminal-style patterns)

---

## 2) Core objects (DocTypes) and how they relate

**A) AlphaX Terminal Driver (Global Catalog)**
- Defines “how” ERP talks to a terminal platform.

**B) AlphaX Bank App Config (Global Catalog)**
- Defines the **Android bank/Mada payment app intent** metadata (package name, actions, extras).
- Used by **Smart POS / Android agent** scenarios.

**C) AlphaX Terminal Brand (Global Catalog)**
- Defines card scheme / brand (MADA, VISA, MASTERCARD, etc.).
- Optionally sets a default Bank App Config.

**D) AlphaX Terminal Device (Per physical device)**
- Represents a physical terminal or an Android agent endpoint (e.g., Aisino A90).
- Stores device_code/topic, MQTT settings, last seen, etc.

**E) AlphaX Payment Terminal Settings (Per Company/Branch/Terminal Profile)**
- Your actual “profile” that binds Company/Branch to a Driver + configuration.

**F) AlphaX Terminal Session (Runtime)**
- One payment attempt lifecycle (PENDING → APPROVED/DECLINED/ERROR).

**G) AlphaX Card Transaction (Audit Log)**
- Stores final metadata for reconciliation (RRN, auth code, terminal id, masked pan, etc.).

---

## 3) Supported deployment patterns

### Pattern 1 — Simulator (recommended for UAT / training)
- No device required.
- Use to validate workflow and approvals.

### Pattern 2 — REST Middleware
- ERP calls a middleware endpoint that talks to the terminal estate.

### Pattern 3 — Android Smart POS (Aisino A90) via Agent + Callback (recommended for KSA banks)
- ERP publishes a request to device agent (MQTT or polling).
- Agent launches bank app via **Android Intent**.
- Agent posts callback to ERP to finalize session.

---

## 4) Step-by-step configuration (Admin checklist)

### Step 1 — Confirm Custom Fields on Mode of Payment
Path: **Accounting → Mode of Payment → (open your Card MoP)**

Required fields (created by fixtures):
- **Capture Terminal Data** (Check)
- **Terminal Settings** (Link: AlphaX Payment Terminal Settings)
- Optional enforcement fields depending on your configuration:
  - Require Terminal Approval
  - Allow Manual Reference

**Best practice**
- Capture Terminal Data = ON
- Require Terminal Approval = ON
- Allow Manual Reference = OFF (enable only for emergency policy)

---

### Step 2 — Configure AlphaX Terminal Drivers (Global)
Path: **AlphaX Card Terminal → AlphaX Terminal Driver**

You will see drivers preloaded by the app.

**Field reference**
- **Driver Code**: stable code (used internally)
- **Driver Name**: human label
- **Handler Path**: Python class (do not change unless development)
- **Capabilities**: SALE / REFUND / VOID, etc.
- **Config Schema**: JSON describing required configuration (admin guidance)

---

### Step 3 — Configure Bank App Configs (Global) — for Aisino/Android only
Path: **AlphaX Card Terminal → AlphaX Bank App Config**

Create one config per bank POS application.

**Fields**
- **Config Code**: unique ID (e.g., MADA_RIYADH_BANKX)
- **Config Name**: friendly name
- **Android Package Name**: bank app package on device (Settings → Apps)
- **Intent Action (SALE)**: Android action string for payment
- **Intent Action (REFUND)**: Android action string for refund
- **Intent Extras (JSON)**: key/value extras sent to bank app. Supports placeholders:
  - `{{amount}}`, `{{currency}}`, `{{uuid}}`, `{{reference.name}}`, `{{reference.doctype}}`
- **Response Mapping (JSON)**: mapping from agent/bank response keys into standard fields:
  - `status`, `rrn`, `auth_code`, `terminal_id`, `merchant_id`, `masked_pan`, `brand`

**Example Intent Extras**
```json
{
  "amount": "{{amount}}",
  "currency": "{{currency}}",
  "invoice": "{{reference.name}}",
  "uuid": "{{uuid}}"
}
```

---

### Step 4 — Configure Brands (Global)
Path: **AlphaX Card Terminal → AlphaX Terminal Brand**

Create one record per scheme:
- MADA
- VISA
- MASTERCARD

**Fields**
- **Brand Code**: (MADA/VISA/etc.)
- **Brand Name**: display name
- **Default Bank App Config**: optional default intent config for that brand

---

### Step 5 — Register the physical terminal device (recommended)
Path: **AlphaX Card Terminal → AlphaX Terminal Device**

For Aisino A90 agent setup:
- **Device Code / Topic**: unique (e.g., AISINO_A90_RYD_01)
- **MQTT Settings**: choose MQTT settings (broker/credentials)
- **Status / Last Seen**: used for monitoring

---

### Step 6 — Create the Terminal Profile (Company/Branch)
Path: **AlphaX Card Terminal → AlphaX Payment Terminal Settings**

Create one record per **Company/Branch/Terminal profile**.

**Fields**
- **Settings Name**: profile name (e.g., “DropEx Riyadh — Mada A90 #1”)
- **Enabled**
- **Company**
- **Branch** (optional)
- **Driver** (Link to AlphaX Terminal Driver)
- **Brand** (optional but recommended)
- **Bank App Config** (Android only)
- **Terminal Device** (optional but recommended)
- **Driver Config (JSON)**: advanced overrides (preferred for drivers like MQTT/Android)
- Network/MID/TID/Timeout fields: for REST/TCP patterns

**Android agent example (Driver Config JSON)**
```json
{
  "device_code": "AISINO_A90_RYD_01",
  "callback_url": "https://<your-site>/api/method/alphax_card_terminal.api.terminal_callback",
  "callback_secret": "<shared-secret>",
  "qos": 1
}
```

---

### Step 7 — Bind Mode of Payment to the Terminal Profile
Path: **Accounting → Mode of Payment**

- Enable **Capture Terminal Data**
- Set **Terminal Settings** = your AlphaX Payment Terminal Settings record
- If you enforce approval: keep “Require Terminal Approval” ON.

---

## 5) Operations: how users use it

### 5.1 Running a payment
- User creates Sales Invoice / POS Invoice
- Selects Card Mode of Payment
- Start capture (button/UI depends on your POS customization)
- Terminal session is created and tracked
- On approval, invoice can be submitted

### 5.2 Monitoring
- **AlphaX Terminal Session**: live/pending sessions
- **AlphaX Card Transaction**: final audit records (used by finance)

---

## 6) Troubleshooting

### Install error: KeyError 'name' (fixtures)
- Ensure fixture records include `"name"` (this app version includes it).

### CaptureRequest instantiation error
- Ensure you are on version **0.0.4+** (CaptureRequest is a dataclass).

### No callback received
- Verify callback_url is reachable from device network
- Verify callback_secret matches device secret
- Check Terminal Device online/last_seen (if heartbeat implemented)

---

## 7) Driver onboarding (how to get drivers)

### Built-in drivers
Installed with the app.

### New bank/provider drivers
Two options:
1) Use **Generic REST** driver with middleware.
2) Implement a new driver class under:
   `alphax_card_terminal/drivers/impl/`

**Do not modify core logic** — add drivers as plugins.

---

## 8) Appendix — Standard async payload (recommended)
ERP publishes request with:
- uuid
- amount/currency
- reference invoice
- brand (optional)
- bank_app_config (optional)
Agent returns callback with:
- status
- rrn/auth_code
- terminal_id/merchant_id
- masked_pan (optional)

---

If you want, we can also provide:
- A printable PDF version of this manual
- A “Go-Live checklist” for branches and devices
- A bank onboarding form to capture package/action/extras for each provider
