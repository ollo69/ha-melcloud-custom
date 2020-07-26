"""The MELCloud Climate integration."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict, List, Optional

from aiohttp import ClientConnectionError, ClientSession
from async_timeout import timeout
from pymelcloud import Device, get_devices
from pymelcloud.client import BASE_URL
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.util import Throttle

from .const import (
    CONF_DISABLE_SENSORS,
    CONF_LANGUAGE,
    DOMAIN,
    LANGUAGES,
    MEL_DEVICES,
    Language,
)

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

PLATFORMS = ["climate", "sensor", "binary_sensor"]

MELCLOUD_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_LANGUAGE): vol.In(LANGUAGES.keys()),
    vol.Optional(CONF_DISABLE_SENSORS, default=False): bool,
    #vol.Required(CONF_TOKEN): cv.string,
})

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: MELCLOUD_SCHEMA
    },
    extra=vol.ALLOW_EXTRA,
)

#BASE_URL = "https://app.melcloud.com/Mitsubishi.Wifi.Client"


class MelCloudAuthentication:
    def __init__(self, email, password, language = Language.English):
        self._email = email
        self._password = password
        self._language = language
        self._contextkey = None

    def isLogin(self):
        return self._contextkey != None
        
    async def login(self, _session: ClientSession):
        _LOGGER.debug("Login ...")

        self._contextkey = None

        if _session is None:
            return False
            
        body = {
            "Email": self._email,
            "Password": self._password,
            "Language": self._language,
            "AppVersion": "1.19.1.1",
            "Persist": False,
            "CaptchaResponse": None,
        }

        async with _session.post(
            f"{BASE_URL}/Login/ClientLogin", json=body, raise_for_status=True
        ) as resp:
            req = await resp.json()
    
        if not req is None:
            if "ErrorId" in req and req["ErrorId"] == None:
                self._contextkey = req.get("LoginData").get("ContextKey")
                return True
            else:
                _LOGGER.error("MELCloud User/Password invalid!")
        else:
            _LOGGER.error("Login to MELCloud failed!")
            
        return False
        
    def getContextKey(self):
        return self._contextkey


async def async_setup(hass: HomeAssistantType, config: ConfigEntry):
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


async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    """Establish connection with MELClooud."""
    conf = entry.data
    username = conf[CONF_USERNAME]
    language = conf[CONF_LANGUAGE]
    mclanguage = LANGUAGES[language]

    _LOGGER.info(
        "Initializing %s platform with user: %s - language: %s(%s).",
        DOMAIN,
        username,
        language,
        str(mclanguage)
    )
    
    mcauth = MelCloudAuthentication(username, conf[CONF_PASSWORD], mclanguage)
    try:
        result = await mcauth.login(hass.helpers.aiohttp_client.async_get_clientsession())
        if not result:
            raise ConfigEntryNotReady()
    except:
        raise ConfigEntryNotReady()

    token = mcauth.getContextKey()
    mel_devices = await mel_devices_setup(hass, token)
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {}).update(
        {
            MEL_DEVICES: mel_devices,
        }
    )
    disable_sensors = conf.get(CONF_DISABLE_SENSORS, False)

    for platform in PLATFORMS:
        if platform == "climate" or not disable_sensors:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    await asyncio.gather(
        *[
            hass.config_entries.async_forward_entry_unload(config_entry, platform)
            for platform in PLATFORMS
        ]
    )
    hass.data[DOMAIN].pop(config_entry.entry_id)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True


class MelCloudDevice:
    """MELCloud Device instance."""

    def __init__(self, device: Device):
        """Construct a device wrapper."""
        self.device = device
        self.name = device.name
        self._available = True

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs):
        """Pull the latest data from MELCloud."""
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
        return self.device._device_conf

    @property
    def wifi_signal(self) -> Optional[int]:
        """Return wifi signal."""
        if self.device._device_conf is None:
            return None
        return self.device._device_conf.get("Device", {}).get("WifiSignalStrength", None)

    @property
    def error_state(self) -> Optional[bool]:
        """Return error_state."""
        if self.device._device_conf is None:
            return None
        device = self.device._device_conf.get("Device", {})
        return device.get("HasError", False)

    @property
    def has_wide_van(self) -> Optional[bool]:
        """Return has wide van info."""
        if self.device._device_conf is None:
            return False
        device = self.device._device_conf.get("Device", {})
        return device.get("HasWideVane", False)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        _device_info = {
            "identifiers": {(DOMAIN, f"{self.device.mac}-{self.device.serial}")},
            "manufacturer": "Mitsubishi Electric",
            "name": self.name,
            "connections": {(CONNECTION_NETWORK_MAC, self.device.mac)},
        }
        model = "MELCloud IF (MAC: %s)" % (self.device.mac)
        unit_infos = self.device.units
        if unit_infos is not None:
            model = model + " - " + ", ".join(
                [x["model"] for x in unit_infos if x["model"]]
            )
        _device_info["model"] = model
        
        return _device_info


async def mel_devices_setup(hass, token) -> List[MelCloudDevice]:
    """Query connected devices from MELCloud."""
    session = hass.helpers.aiohttp_client.async_get_clientsession()
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

    wrapped_devices = {}
    for device_type, devices in all_devices.items():
        wrapped_devices[device_type] = [MelCloudDevice(device) for device in devices]
    return wrapped_devices
