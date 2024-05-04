"""Support for MelCloud device sensors."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Callable

from pymelcloud import DEVICE_TYPE_ATA, DEVICE_TYPE_ATW
from pymelcloud.atw_device import Zone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfEnergy,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MelCloudDevice
from .const import DOMAIN, MEL_DEVICES


@dataclass
class MelcloudRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[Any], float]
    enabled: Callable[[Any], bool]


@dataclass
class MelcloudSensorEntityDescription(
    SensorEntityDescription, MelcloudRequiredKeysMixin
):
    """Describes Melcloud sensor entity."""


ATA_SENSORS: tuple[MelcloudSensorEntityDescription, ...] = (
    MelcloudSensorEntityDescription(
        key="wifi_signal",
        name="WiFi Signal",
        icon="mdi:signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.wifi_signal,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="room_temperature",
        name="Room Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.device.room_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="energy",
        name="Energy",
        icon="mdi:factory",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda x: x.device.total_energy_consumed,
        enabled=lambda x: x.device.has_energy_consumed_meter,
        entity_registry_enabled_default=False,
    ),
)
ATW_SENSORS: tuple[MelcloudSensorEntityDescription, ...] = (
    MelcloudSensorEntityDescription(
        key="outside_temperature",
        name="Outside Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.device.outside_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="tank_temperature",
        name="Tank Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.device.tank_temperature,
        enabled=lambda x: True,
    ),
)
ATW_ZONE_SENSORS: tuple[MelcloudSensorEntityDescription, ...] = (
    MelcloudSensorEntityDescription(
        key="room_temperature",
        name="Room Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda zone: zone.room_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="flow_temperature",
        name="Flow Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda zone: zone.flow_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="return_temperature",
        name="Flow Return Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda zone: zone.return_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up MELCloud device sensors based on config_entry."""
    entry_config = hass.data[DOMAIN][entry.entry_id]

    mel_devices = entry_config.get(MEL_DEVICES)
    entities = []
    entities.extend(
        [
            MelDeviceSensor(mel_device, description)
            for description in ATA_SENSORS
            for mel_device in mel_devices[DEVICE_TYPE_ATA]
            if description.enabled(mel_device)
        ]
        + [
            MelDeviceSensor(mel_device, description)
            for description in ATW_SENSORS
            for mel_device in mel_devices[DEVICE_TYPE_ATW]
            if description.enabled(mel_device)
        ]
    )
    entities.extend(
        [
            AtwZoneSensor(mel_device, zone, description)
            for mel_device in mel_devices[DEVICE_TYPE_ATW]
            for zone in mel_device.device.zones
            for description in ATW_ZONE_SENSORS
            if description.enabled(zone)
        ]
    )
    async_add_entities(entities, False)


class MelDeviceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    entity_description: MelcloudSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        api: MelCloudDevice,
        description: MelcloudSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(api.coordinator)
        self._api = api
        self.entity_description = description

        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-{description.key}"
        self._attr_device_info = api.device_info
        self._attr_extra_state_attributes = api.extra_attributes

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._api)


class AtwZoneSensor(MelDeviceSensor):
    """Air-to-Air device sensor."""

    def __init__(
        self,
        api: MelCloudDevice,
        zone: Zone,
        description: MelcloudSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        if zone.zone_index != 1:
            description.key = f"{description.key}-zone-{zone.zone_index}"
        super().__init__(api, description)

        self._attr_device_info = api.zone_device_info(zone)
        self._zone = zone

    @property
    def native_value(self):
        """Return zone based state."""
        return self.entity_description.value_fn(self._zone)
