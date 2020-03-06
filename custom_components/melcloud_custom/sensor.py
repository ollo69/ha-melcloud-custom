"""Support for MelCloud device sensors."""
import logging

from pymelcloud.const import DEVICE_TYPE_ATA

from homeassistant.const import DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS, STATE_ON, STATE_OFF
from homeassistant.components.binary_sensor import DEVICE_CLASS_PROBLEM
from homeassistant.helpers.entity import Entity

from . import MelCloudDevice
from .const import DOMAIN, MEL_DEVICES, TEMP_UNIT_LOOKUP, WIFI_SIGNAL, ROOM_TEMPERATURE, ENERGY, ERROR_STATE

ATTR_MEASUREMENT_NAME = "measurement_name"
ATTR_ICON = "icon"
ATTR_UNIT_FN = "unit_fn"
ATTR_DEVICE_CLASS = "device_class"
ATTR_VALUE_FN = "value_fn"
ATTR_ENABLED_FN = "enabled"

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

SENSORS = {
    WIFI_SIGNAL: {
        ATTR_MEASUREMENT_NAME: "WiFi Signal",
        ATTR_ICON: "mdi:signal",
        ATTR_UNIT_FN: lambda x: "dBm",
        ATTR_DEVICE_CLASS: None,
        ATTR_VALUE_FN: lambda x: x.wifi_signal,
        ATTR_ENABLED_FN: lambda x: True,
    },
    ROOM_TEMPERATURE: {
        ATTR_MEASUREMENT_NAME: "Room Temperature",
        ATTR_ICON: "mdi:thermometer",
        ATTR_UNIT_FN: lambda x: TEMP_UNIT_LOOKUP.get(x.device.temp_unit, TEMP_CELSIUS),
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_VALUE_FN: lambda x: x.device.room_temperature,
        ATTR_ENABLED_FN: lambda x: True,
    },
    ENERGY: {
        ATTR_MEASUREMENT_NAME: "Energy",
        ATTR_ICON: "mdi:factory",
        ATTR_UNIT_FN: lambda x: "kWh",
        ATTR_DEVICE_CLASS: None,
        ATTR_VALUE_FN: lambda x: x.device.total_energy_consumed,
        ATTR_ENABLED_FN: lambda x: x.device.has_energy_consumed_meter,
    },
}

BINARY_SENSORS = {
    ERROR_STATE: {
        ATTR_MEASUREMENT_NAME: "Error State",
        ATTR_ICON: None,
        ATTR_UNIT_FN: lambda x: None,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_PROBLEM,
        ATTR_VALUE_FN: lambda x: x.error_state,
        ATTR_ENABLED_FN: lambda x: True,
    },
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_sensors(hass, entry, async_add_entities, type_binary):
    """Set up MELCloud device sensors based on config_entry."""
    sensors_list = BINARY_SENSORS if type_binary else SENSORS
    
    mel_devices = hass.data[DOMAIN][entry.entry_id].get(MEL_DEVICES)
    async_add_entities(
        [
            MelCloudSensor(mel_device, measurement, definition, type_binary)
            for measurement, definition in sensors_list.items()
            for mel_device in mel_devices[DEVICE_TYPE_ATA]
            if definition[ATTR_ENABLED_FN](mel_device) and hass.data[DOMAIN][entry.entry_id][measurement]
        ],
        True,
    )

async def async_setup_entry(hass, entry, async_add_entities):
    await async_setup_sensors(hass, entry, async_add_entities, False)

class MelCloudSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, device: MelCloudDevice, measurement, definition, isbinary):
        """Initialize the sensor."""
        self._api = device
        self._name_slug = device.name
        self._measurement = measurement
        self._def = definition
        self._isbinary = isbinary

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._api.device.serial}-{self._api.device.mac}-{self._measurement}"

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._def[ATTR_ICON]

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name_slug} {self._def[ATTR_MEASUREMENT_NAME]}"

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        if self._isbinary:
            return self._def[ATTR_VALUE_FN](self._api)
            
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._isbinary:
            return STATE_ON if self.is_on else STATE_OFF

        return self._def[ATTR_VALUE_FN](self._api)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._def[ATTR_UNIT_FN](self._api)

    @property
    def device_class(self):
        """Return device class."""
        return self._def[ATTR_DEVICE_CLASS]

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data={}
        data[ATTR_STATE_DEVICE_ID] = self._api.device_id
        data[ATTR_STATE_DEVICE_SERIAL] = self._api.device.serial
        data[ATTR_STATE_DEVICE_MAC] = self._api.device.mac
        #data[ATTR_DEVICE_LAST_SEEN] = self._api.device.last_seen
        
        unit_infos = self._api.device.units
        if unit_infos is not None:
            for i, u in enumerate(unit_infos):
                if i < 2:
                    data[ATTR_STATE_DEVICE_UNIT[i][ATTR_STATE_UMODEL]] = u[ATTR_STATE_UMODEL]
                    data[ATTR_STATE_DEVICE_UNIT[i][ATTR_STATE_USERIAL]] = u[ATTR_STATE_USERIAL]
        
        return data
