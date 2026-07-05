# hacs-telnyx

HACS installable Telnyx Home Assistant component with ConfigFlow setup, Telnyx webhook handling, notify entities for messaging and voice, and automation-friendly services for DTMF and recording control.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=teagan42&repository=hacs-telnyx&category=integration)
[![Open your Home Assistant instance and start setting up Telnyx](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=telnyx)

## Features

- ConfigFlow-based setup for Telnyx credentials, a Call Control connection ID, and default voice/messaging targets
- Notify entities for:
  - Messaging
  - Voice TeXML
  - Voice API
- Domain services for:
  - `telnyx.send_sms`
  - `telnyx.send_texml`
  - `telnyx.send_voice_api`
  - `telnyx.send_dtmf`
  - `telnyx.start_recording`
  - `telnyx.stop_recording`
- Automatic Home Assistant webhook listener registration
- Verified Telnyx webhook handling with transcription events for automations
- Webhook events for general Telnyx payloads and transcription-driven automations

## Events fired by webhooks

Every verified incoming Telnyx webhook fires one or both of the following Home Assistant events, which automations can trigger off of.

### `telnyx_event`

Fired for **every** valid incoming webhook payload.

| Field | Description |
|---|---|
| `entry_id` | Config entry that received the webhook |
| `event_type` | Telnyx event type string (e.g. `message.received`, `call.initiated`) |
| `payload` | Full raw webhook payload |

```yaml
trigger:
  - platform: event
    event_type: telnyx_event
    event_data:
      event_type: message.received  # optional — omit to match all events
```

The full payload is available as `{{ trigger.event.data.payload }}` inside the automation.

### `telnyx_transcription`

Fired only when the webhook payload contains a transcription string (e.g. after a call transcription completes).

| Field | Description |
|---|---|
| `entry_id` | Config entry that received the webhook |
| `event_type` | Telnyx event type string |
| `payload` | Full raw webhook payload |
| `transcription` | Extracted transcription text |
| `call_control_id` | Associated call control ID |

```yaml
trigger:
  - platform: event
    event_type: telnyx_transcription
```

The transcription text is available as `{{ trigger.event.data.transcription }}` inside the automation.

## Automation example

Listen for the `telnyx_transcription` event and then call `telnyx.send_dtmf`, `telnyx.start_recording`, or `telnyx.stop_recording` in your automation.
