"""The MELCloud Climate integration."""
from __future__ import annotations

from aiohttp import ClientConnectionError
import asyncio
from async_timeout import timeout
from collections.abc import Iterable
from datetime import timedelta
import logging
from typing import Any, Dict, Optional

from pymelcloud import Device, get_devices
from pymelcloud.client import BASE_URL
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    ATTR_MODEL,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_TOKEN,
    MAJOR_VERSION,
    MINOR_VERSION,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import Throttle

from .const import (
    CONF_LANGUAGE,
    DOMAIN,
    LANGUAGES,
    MEL_DEVICES,
    Language,
)

ATTR_STATE_DEVICE_ID = "device_id"
ATTR_STATE_DEVICE_SERIAL = "device_serial"
ATTR_STATE_DEVICE_MAC = "device_mac"
ATTR_STATE_DEVICE_LAST_SEEN = "last_communication"

ATTR_STATE_UMODEL = "model"
ATTR_STATE_USERIAL = "serial_number"

ATTR_STATE_DEVICE_UNIT = [
    {
      ATTR_STATE_UMODEL: "unit",
      ATTR_STATE_USERIAL: "unit_serial",
    },
    {
      ATTR_STATE_UMODEL: "ext_unit",
      ATTR_STATE_USERIAL: "ext_unit_serial",
    },
]

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR]

MELCLOUD_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_LANGUAGE): vol.In(LANGUAGES.keys()),
})

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: MELCLOUD_SCHEMA
    },
    extra=vol.ALLOW_EXTRA,
)

# BASE_URL = "https://app.melcloud.com/Mitsubishi.Wifi.Client"


class MelCloudAuthentication:
    """Manage authentication to MelCloud retrieving a valid token."""

    def __init__(self, email, password, language=Language.English):
        """Init MelCloudAuthentication."""
        self._email = email
        self._password = password
        self._language = language
        self._context_key = None

    async def login(self, hass: HomeAssistant):
        """Try login MelCloud with provided credential."""
        _LOGGER.debug("Login ...")

        self._context_key = None
        session = async_get_clientsession(hass)

        body = {
            "Email": self._email,
            "Password": self._password,
            "Language": self._language,
            "AppVersion": "1.19.1.1",
            "Persist": True,
            "CaptchaResponse": None,
        }

        async with session.post(
            f"{BASE_URL}/Login/ClientLogin", json=body, raise_for_status=True
        ) as resp:
            req = await resp.json()
    
        if req is not None:
            if "ErrorId" in req:
                if req["ErrorId"] is not None:
                    _LOGGER.error("MELCloud User/Password invalid!")
                    return False
                if "LoginData" in req:
                    if context_key := req["LoginData"].get("ContextKey"):
                        self._context_key = context_key
                        return True

        _LOGGER.error("Login to MELCloud failed!")
        return False

    @property
    def auth_token(self):
        """Get the authorization token."""
        return self._context_key


def is_min_ha_version(min_ha_major_ver: int, min_ha_minor_ver: int) -> bool:
    """Check if HA version at least a specific version."""
    return (
        MAJOR_VERSION > min_ha_major_ver or
        (MAJOR_VERSION == min_ha_major_ver and MINOR_VERSION >= min_ha_minor_ver)
    )


async def async_setup_entity_platforms(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    platforms: Iterable[Platform | str],
) -> None:
    """Set up entity platforms using new method from HA version 2022.8."""
    if is_min_ha_version(2022, 8):
        await hass.config_entries.async_forward_entry_setups(config_entry, platforms)
    else:
        hass.config_entries.async_setup_platforms(config_entry, platforms)


async def _async_migrate_config(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Migrate config entry storing token instead of username and password"""
    conf = entry.data
    username = conf[CONF_USERNAME]
    language = conf[CONF_LANGUAGE]
    mc_language = LANGUAGES[language]

    _LOGGER.info(
        "Migrating %s platform config with user: %s - language: %s(%s).",
        DOMAIN,
        username,
        language,
        str(mc_language)
    )

    mcauth = MelCloudAuthentication(username, conf[CONF_PASSWORD], mc_language)
    try:
        result = await mcauth.login(hass)
        if not result:
            raise ConfigEntryNotReady()
    except Exception as ex:
        raise ConfigEntryNotReady() from ex

    token = mcauth.auth_token
    hass.config_entries.async_update_entry(entry, data={CONF_TOKEN: token})
    return token


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Establish connection with MELCloud."""
    if DOMAIN not in config:
        return True

    conf = config.get(DOMAIN)
    
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=conf,
        )
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Establish connection with MELCloud."""
    conf = entry.data
    if CONF_TOKEN not in conf:
        token = await _async_migrate_config(hass, entry)
    else:
        token = conf[CONF_TOKEN]

    mel_devices = await mel_devices_setup(hass, token)
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {}).update(
        {
            MEL_DEVICES: mel_devices,
        }
    )
    await async_setup_entity_platforms(hass, entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    ):
        hass.data[DOMAIN].pop(config_entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok


class MelCloudDevice:
    """MELCloud Device instance."""

    def __init__(self, device: Device):
        """Construct a device wrapper."""
        self.device = device
        self.name: Optional[str] = device.name
        self._available = True
        self._extra_attributes = None
        self._dev_conf = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs):
        """Pull the latest data from MELCloud."""
        self._dev_conf = None
        try:
            await self.device.update()
            self._available = True
        except ClientConnectionError:
            _LOGGER.warning("Connection failed for %s", self.name)
            self._available = False

    async def async_set(self, properties: Dict[str, Any]):
        """Write state changes to the MELCloud API."""
        try:
            await self.device.set(properties)
            self._available = True
        except ClientConnectionError:
            _LOGGER.warning("Connection failed for %s", self.name)
            self._available = False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def device_id(self):
        """Return device ID."""
        return self.device.device_id

    @property
    def building_id(self):
        """Return building ID of the device."""
        return self.device.building_id

    @property
    def device_conf(self):
        """Return device_conf of the device."""
        if self._dev_conf is None:
            dev_conf = self.device._device_conf
            if dev_conf is None:
                self._dev_conf = {}
            else:
                self._dev_conf = dev_conf.get("Device", {})
        return self._dev_conf

    @property
    def wifi_signal(self) -> Optional[int]:
        """Return wifi signal."""
        return self.device_conf.get("WifiSignalStrength")

    @property
    def error_state(self) -> Optional[bool]:
        """Return error_state."""
        if not self.device_conf:
            return None
        return self.device_conf.get("HasError", False)

    @property
    def has_wide_van(self) -> Optional[bool]:
        """Return has wide van info."""
        return self.device_conf.get("HasWideVane", False)

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        _device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self.device.mac}-{self.device.serial}")},
            manufacturer="Mitsubishi Electric",
            name=self.name,
            connections={(CONNECTION_NETWORK_MAC, self.device.mac)},
        )
        model = f"MELCloud IF (MAC: {self.device.mac})"
        unit_infos = self.device.units
        if unit_infos is not None:
            model = model + " - " + ", ".join(
                [x["model"] for x in unit_infos if x["model"]]
            )
        _device_info[ATTR_MODEL] = model
        
        return _device_info

    @property
    def extra_attributes(self):
        """Return the optional state attributes."""
        if self._extra_attributes:
            return self._extra_attributes

        data = {
            ATTR_STATE_DEVICE_ID: self.device_id,
            ATTR_STATE_DEVICE_SERIAL: self.device.serial,
            ATTR_STATE_DEVICE_MAC: self.device.mac,
            # data[ATTR_DEVICE_LAST_SEEN] = self._api.device.last_seen
        }

        unit_infos = self.device.units
        if unit_infos is not None:
            for i, u in enumerate(unit_infos):
                if i < 2:
                    data[ATTR_STATE_DEVICE_UNIT[i][ATTR_STATE_UMODEL]] = u[ATTR_STATE_UMODEL]
                    data[ATTR_STATE_DEVICE_UNIT[i][ATTR_STATE_USERIAL]] = u[ATTR_STATE_USERIAL]
            self._extra_attributes = data

        return data


async def mel_devices_setup(hass: HomeAssistant, token: str) -> dict[str, list[MelCloudDevice]]:
    """Query connected devices from MELCloud."""
    session = async_get_clientsession(hass)
    try:
        with timeout(10):
            all_devices = await get_devices(
                token,
                session,
                conf_update_interval=timedelta(minutes=5),
                device_set_debounce=timedelta(seconds=1),
            )
    except (asyncio.TimeoutError, ClientConnectionError) as ex:
        raise ConfigEntryNotReady() from ex

    wrapped_devices: dict[str, list[MelCloudDevice]] = {}
    for device_type, devices in all_devices.items():
        wrapped_devices[device_type] = [MelCloudDevice(device) for device in devices]
    return wrapped_devices
