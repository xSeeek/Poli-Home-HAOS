"""Constants for the Poli Home integration."""

DOMAIN = "poli_home"

# --- API Configuration (from APK decompilation) ---
BASE_URL = "https://AA-Brands.yaleconnect-services.com/api/YaleConnect/"

# Auth header name used by the API
AUTH_HEADER = "access-token"

# Brand + Platform identifier (required header for all requests)
# Format: "{brandToken}.{platformToken}"
BRAND_TOKEN = "B1976672-2AE7-11ED-A261-0242AC120002"
PLATFORM_TOKEN = "3939e0f2-08e5-4bb1-b3a6-ddb1183666d3"
BRAND_PLATFORM_GUID = f"{BRAND_TOKEN}.{PLATFORM_TOKEN}"
BRAND_PLATFORM_HEADER = "brandPlatformGUID"

# Brand ID (numeric)
BRAND_ID = 3

# --- API Endpoints ---
# Account
ENDPOINT_LOGIN = "Account/Login"
ENDPOINT_LOGOUT = "Account/AppLogout"
ENDPOINT_STORE_ACCOUNT = "Account/StoreAccount"
ENDPOINT_CHANGE_PASSWORD = "Account/ChangePassword"
ENDPOINT_SECURITY_PIN = "Account/UpdateSecurityPin"
ENDPOINT_VALIDATE_SECURITY_PIN = "Account/ValidateSecurityPin"
ENDPOINT_GET_SECURITY_PROPERTIES = "Account/GetSecurityProperties"
ENDPOINT_VERIFIED_ACTIVATION = "Account/VerifiedActivation"
ENDPOINT_GET_INTEGRATIONS_STATUS = "Account/GetIntegrationsStatus"

# DoorLock
ENDPOINT_DOORLOCK_LOCK_UNLOCK = "DoorLock/DoorlockLockUnlock"
ENDPOINT_DOORLOCK_ENROLLMENT_START = "Doorlock/DoorlockEnrollmentStart"
ENDPOINT_DOORLOCK_ENROLLMENT_CANCEL = "DoorLock/EnrollmentCancel"
ENDPOINT_DOORLOCK_GET_ALL_MODELS = "Doorlock/GetAllDoorlockModels"

# Device
ENDPOINT_SWITCH_LOCK_UNLOCK = "Device/SwitchLockUnlock"
ENDPOINT_SWITCH_ENROLLMENT_START = "Device/SwitchEnrollmentStart"
ENDPOINT_GET_DEVICE_CATEGORIES = "Device/GetDeviceCategories"
ENDPOINT_GET_DEVICE_PREFIXES = "Device/GetDevicePrefixs"
ENDPOINT_UPDATE_FIRMWARE = "Device/UpdateLastDeviceFirmwareVersion"

# App
ENDPOINT_GET_CONFIGURATION = "App/GetConfiguration"
ENDPOINT_GET_MQTT_CONFIGURATION = "App/GetMqttConfiguration"
ENDPOINT_GET_HUB_CLOUD_IP = "App/GetHubCloudIP"

# Notifications
ENDPOINT_ENUM_NOTIFICATIONS = "Notification/EnumNotifications"
ENDPOINT_GET_ALARMS_BY_DEVICE = "Notification/GetAlarmsByDeviceID"
ENDPOINT_GET_ALARMS_BY_DATE = "Notification/GetAlarmsByDate"
ENDPOINT_DELETE_ALL_NOTIFICATIONS = "Notification/DeleteAllNotificationsForAccount"
ENDPOINT_MARK_NOTIFICATION_READ = "Notification/MarkNotificationAsRead"
ENDPOINT_MARK_ALL_NOTIFICATIONS_READ = "Notification/MarkAllNotificationAsRead"
ENDPOINT_SEND_RECOVER_PASSWORD = "Notification/SendRecoverPasswordEmail"
ENDPOINT_RESEND_EMAIL = "Notification/ResendEmail"

# Access Control
ENDPOINT_ACCESS_REGISTERS = "AccessControl/GetAccessRegistersForHome"

# --- Integration defaults ---
DEFAULT_SCAN_INTERVAL = 300  # seconds between status polls
REQUEST_TIMEOUT = 30  # seconds

# --- Config flow keys ---
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
