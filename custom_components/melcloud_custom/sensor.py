"""Support for MelCloud device sensors."""
import logging

from pymelcloud import DEVICE_TYPE_ATA, DEVICE_TYPE_ATW
from pymelcloud.atw_device import Zone

from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    TEMP_CELSIUS,
    STATE_ON,
    STATE_OFF
)
from homeassistant.components.binary_sensor import DEVICE_CLASS_PROBLEM
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

from . import MelCloudDevice
from .const import DOMAIN, MEL_DEVICES

ATTR_MEASUREMENT_NAME = "measurement_name"
ATTR_ICON = "icon"
ATTR_UNIT = "unit"
ATTR_DEVICE_CLASS = "device_class"
ATTR_VALUE_FN = "value_fn"
ATTR_ENABLED_FN = "enabled"
ATTR_ENABLED_DEF = "enabled_default"

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

ATA_SENSORS = {
    "wifi_signal": {
        ATTR_MEASUREMENT_NAME: "WiFi Signal",
        ATTR_ICON: "mdi:signal",
        ATTR_UNIT: "dBm",
        ATTR_DEVICE_CLASS: None,
        ATTR_VALUE_FN: lambda x: x.wifi_signal,
        ATTR_ENABLED_FN: lambda x: True,
    },
    "room_temperature": {
        ATTR_MEASUREMENT_NAME: "Room Temperature",
        ATTR_ICON: "mdi:thermometer",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_VALUE_FN: lambda x: x.device.room_temperature,
        ATTR_ENABLED_FN: lambda x: True,
    },
    "energy": {
        ATTR_MEASUREMENT_NAME: "Energy",
        ATTR_ICON: "mdi:factory",
        ATTR_UNIT: ENERGY_KILO_WATT_HOUR,
        ATTR_DEVICE_CLASS: None,
        ATTR_VALUE_FN: lambda x: x.device.total_energy_consumed,
        ATTR_ENABLED_FN: lambda x: x.device.has_energy_consumed_meter,
    },
}

ATA_BINARY_SENSORS = {
    "error_state": {
        ATTR_MEASUREMENT_NAME: "Error State",
        ATTR_ICON: None,
        ATTR_UNIT: None,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_PROBLEM,
        ATTR_VALUE_FN: lambda x: x.error_state,
        ATTR_ENABLED_FN: lambda x: True,
        ATTR_ENABLED_DEF: True,
    },
}

ATW_SENSORS = {
    "outside_temperature": {
        ATTR_MEASUREMENT_NAME: "Outside Temperature",
        ATTR_ICON: "mdi:thermometer",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_VALUE_FN: lambda x: x.device.outside_temperature,
        ATTR_ENABLED_FN: lambda x: True,
    },
    "tank_temperature": {
        ATTR_MEASUREMENT_NAME: "Tank Temperature",
        ATTR_ICON: "mdi:thermometer",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_VALUE_FN: lambda x: x.device.tank_temperature,
        ATTR_ENABLED_FN: lambda x: True,
        ATTR_ENABLED_DEF: True,
    },
}

ATW_ZONE_SENSORS = {
    "room_temperature": {
        ATTR_MEASUREMENT_NAME: "Room Temperature",
        ATTR_ICON: "mdi:thermometer",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_VALUE_FN: lambda zone: zone.room_temperature,
        ATTR_ENABLED_FN: lambda x: True,
    },
    "flow_temperature": {
        ATTR_MEASUREMENT_NAME: "Flow Temperature",
        ATTR_ICON: "mdi:thermometer",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_VALUE_FN: lambda zone: zone.flow_temperature,
        ATTR_ENABLED_FN: lambda x: True,
    },
    "return_temperature": {
        ATTR_MEASUREMENT_NAME: "Flow Return Temperature",
        ATTR_ICON: "mdi:thermometer",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_VALUE_FN: lambda zone: zone.return_temperature,
        ATTR_ENABLED_FN: lambda x: True,
    },
}

_LOGGER = logging.getLogger(__name__)


@callback
def setup_sensors(hass, entry, async_add_entities, type_binary, init_status=False):
    """Set up MELCloud device sensors and bynary sensor based on config_entry."""
    entry_config = hass.data[DOMAIN][entry.entry_id]
    ata_sensors = ATA_BINARY_SENSORS if type_binary else ATA_SENSORS
    atw_sensors = {} if type_binary else ATW_SENSORS

    mel_devices = entry_config.get(MEL_DEVICES)
    entities = []
    entities.extend(
        [
            MelDeviceSensor(mel_device, measurement, definition, type_binary)
            for measurement, definition in ata_sensors.items()
            for mel_device in mel_devices[DEVICE_TYPE_ATA]
            if definition[ATTR_ENABLED_FN](mel_device)
        ]
        + [
            MelDeviceSensor(mel_device, measurement, definition, type_binary)
            for measurement, definition in atw_sensors.items()
            for mel_device in mel_devices[DEVICE_TYPE_ATW]
            if definition[ATTR_ENABLED_FN](mel_device)
        ]
    )
    entities.extend(
        [
            AtwZoneSensor(mel_device, zone, measurement, definition)
            for mel_device in mel_devices[DEVICE_TYPE_ATW]
            for zone in mel_device.device.zones
            for measurement, definition, in ATW_ZONE_SENSORS.items()
            if definition[ATTR_ENABLED_FN](zone) and not type_binary
        ]
    )
    async_add_entities(entities, init_status)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up MELCloud device sensors based on config_entry."""
    setup_sensors(hass, entry, async_add_entities, False)


class MelDeviceSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, device: MelCloudDevice, measurement, definition, is_binary):
        """Initialize the sensor."""
        self._api = device
        self._name_slug = device.name
        self._measurement = measurement
        self._def = definition
        self._is_binary = is_binary

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._def.get(ATTR_ENABLED_DEF, False)

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
        if self._is_binary:
            return self._def[ATTR_VALUE_FN](self._api)
            
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._is_binary:
            return STATE_ON if self.is_on else STATE_OFF

        return self._def[ATTR_VALUE_FN](self._api)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._def[ATTR_UNIT]

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
        data = {
            ATTR_STATE_DEVICE_ID: self._api.device_id,
            ATTR_STATE_DEVICE_SERIAL: self._api.device.serial,
            ATTR_STATE_DEVICE_MAC: self._api.device.mac,
            # data[ATTR_DEVICE_LAST_SEEN] = self._api.device.last_seen
        }

        unit_infos = self._api.device.units
        if unit_infos is not None:
            for i, u in enumerate(unit_infos):
                if i < 2:
                    data[ATTR_STATE_DEVICE_UNIT[i][ATTR_STATE_UMODEL]] = u[ATTR_STATE_UMODEL]
                    data[ATTR_STATE_DEVICE_UNIT[i][ATTR_STATE_USERIAL]] = u[ATTR_STATE_USERIAL]

        return data


class AtwZoneSensor(MelDeviceSensor):
    """Air-to-Air device sensor."""

    def __init__(
        self, api: MelCloudDevice, zone: Zone, measurement, definition,
    ):
        """Initialize the sensor."""
        super().__init__(api, measurement, definition, False)
        self._zone = zone
        self._name_slug = f"{api.name} {zone.name}"

    @property
    def state(self):
        """Return zone based state."""
        return self._def[ATTR_VALUE_FN](self._zone)
