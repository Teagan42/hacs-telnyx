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

## Automation example

Listen for the `telnyx_transcription` event and then call `telnyx.send_dtmf`, `telnyx.start_recording`, or `telnyx.stop_recording` in your automation.
