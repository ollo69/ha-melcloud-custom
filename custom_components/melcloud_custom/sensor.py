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
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfEnergy,
    UnitOfTemperature,
)
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
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        value_fn=lambda x: x.wifi_signal,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="room_temperature",
        name="Room Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda x: x.device.room_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="energy",
        name="Energy",
        icon="mdi:factory",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda x: x.device.total_energy_consumed,
        enabled=lambda x: x.device.has_energy_consumed_meter,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="daily_energy",
        name="Daily Energy Consumed",
        icon="mdi:factory",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda x: x.device.daily_energy_consumed,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
)
ATW_SENSORS: tuple[MelcloudSensorEntityDescription, ...] = (
    MelcloudSensorEntityDescription(
        key="daily_heating_energy_consumed",
        name="Daily Heating Energy Consumed",
        icon="mdi:heat-pump",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda x: x.daily_heating_energy_consumed,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="daily_cooling_energy_consumed",
        name="Daily Cooling Energy Consumed",
        icon="mdi:sun-snowflake",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda x: x.daily_cooling_energy_consumed,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="daily_heating_energy_produced",
        name="Daily Heating Energy Produced",
        icon="mdi:factory",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda x: x.daily_heating_energy_produced,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="daily_cooling_energy_produced",
        name="Daily Cooling Energy Produced",
        icon="mdi:factory",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda x: x.daily_cooling_energy_produced,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="wifi_signal",
        name="WiFi Signal",
        icon="mdi:signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        value_fn=lambda x: x.wifi_signal,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="outside_temperature",
        name="Outside Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda x: x.device.outside_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="tank_temperature",
        name="Tank Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda x: x.device.tank_temperature,
        enabled=lambda x: x.device_info.get("HasHotWaterTank", False),
    ),
)
ATW_ZONE_SENSORS: tuple[MelcloudSensorEntityDescription, ...] = (
    MelcloudSensorEntityDescription(
        key="room_temperature",
        name="Room Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda zone: zone.room_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="flow_temperature",
        name="Flow Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda zone: zone.flow_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
    MelcloudSensorEntityDescription(
        key="return_temperature",
        name="Flow Return Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda zone: zone.return_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=False,
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
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

    def __init__(
        self,
        api: MelCloudDevice,
        description: MelcloudSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(api.coordinator)
        self._api = api
        self.entity_description = description

        self._attr_name = f"{api.name} {description.name}"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-{description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._api)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""
        return self._api.extra_attributes


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
        self._zone = zone
        self._attr_name = f"{api.name} {zone.name} {description.name}"

    @property
    def native_value(self):
        """Return zone based state."""
        return self.entity_description.value_fn(self._zone)
