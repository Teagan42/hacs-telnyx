# hacs-telnyx

HACS installable Telnyx Home Assistant component with ConfigFlow setup, Telnyx webhook handling, notify entities for messaging and voice, and automation-friendly services for DTMF and recording control.

[![Open your Home Assistant instance and add this repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=https://github.com/Teagan42/hacs-telnyx)
[![Open your Home Assistant instance and start setting up Telnyx](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=telnyx)

## Features

- ConfigFlow-based setup for Telnyx credentials and default voice/messaging targets
- Notify entities for:
  - Messaging
  - Voice TexML
  - Voice API
- Domain services for:
  - `telnyx.send_sms`
  - `telnyx.send_texml`
  - `telnyx.send_voice_api`
  - `telnyx.send_dtmf`
  - `telnyx.start_recording`
  - `telnyx.stop_recording`
- Automatic Home Assistant webhook registration
- Webhook events for general Telnyx payloads and transcription-driven automations

## Automation example

Listen for the `telnyx_transcription` event and then call `telnyx.send_dtmf`, `telnyx.start_recording`, or `telnyx.stop_recording` in your automation.
