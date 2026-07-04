"""Constants for the Telnyx integration."""

from homeassistant.const import Platform

DOMAIN = "telnyx"
PLATFORMS = (Platform.NOTIFY,)

CONF_API_KEY = "api_key"
CONF_DEFAULT_MESSAGING_FROM = "default_messaging_from"
CONF_DEFAULT_MESSAGING_TO = "default_messaging_to"
CONF_DEFAULT_VOICE_FROM = "default_voice_from"
CONF_DEFAULT_VOICE_TO = "default_voice_to"
CONF_MESSAGING_PROFILE_ID = "messaging_profile_id"
CONF_WEBHOOK_ID = "webhook_id"
CONF_WEBHOOK_PUBLIC_KEY = "webhook_public_key"

ATTR_CALL_CONTROL_ID = "call_control_id"
ATTR_CHANNELS = "channels"
ATTR_DIGITS = "digits"
ATTR_ENTRY_ID = "entry_id"
ATTR_EVENT_TYPE = "event_type"
ATTR_FROM = "from"
ATTR_FORMAT = "format"
ATTR_MESSAGE = "message"
ATTR_PAYLOAD = "payload"
ATTR_TEXML = "texml"
ATTR_TO = "to"
ATTR_TRANSCRIPTION = "transcription"

DEFAULT_NAME = "Telnyx"
EVENT_TELNYX = "telnyx_event"
EVENT_TELNYX_TRANSCRIPTION = "telnyx_transcription"

SERVICE_SEND_SMS = "send_sms"
SERVICE_SEND_TEXML = "send_texml"
SERVICE_SEND_VOICE_API = "send_voice_api"
SERVICE_SEND_DTMF = "send_dtmf"
SERVICE_START_RECORDING = "start_recording"
SERVICE_STOP_RECORDING = "stop_recording"
