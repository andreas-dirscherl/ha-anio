"""Constants for the Anio Smartwatch integration."""

DOMAIN = "anio"
MANUFACTURER = "Anio"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_APP_UUID = "app_uuid"

DEFAULT_NAME = "Anio Watch"
DEFAULT_SCAN_INTERVAL = 120  # seconds (2 minutes)
MIN_SCAN_INTERVAL = 30  # seconds
MAX_SCAN_INTERVAL = 3600  # seconds (1 hour)

BASE_URL = "https://api.anio.cloud"
CLIENT_ID = "ANIO"
ACCEPT_LANGUAGE = "de"
