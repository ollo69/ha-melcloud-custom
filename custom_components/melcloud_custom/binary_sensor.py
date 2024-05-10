"""Support for MelCloud device binary sensors."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Callable

from pymelcloud import DEVICE_TYPE_ATA

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MelCloudDevice
from .const import DOMAIN, MEL_DEVICES


@dataclass
class MelcloudRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[Any], bool]
    enabled: Callable[[Any], bool]


@dataclass
class MelcloudBinarySensorEntityDescription(
    BinarySensorEntityDescription, MelcloudRequiredKeysMixin
):
    """Describes Melcloud binary sensor entity."""


ATA_BINARY_SENSORS: tuple[MelcloudBinarySensorEntityDescription, ...] = (
    MelcloudBinarySensorEntityDescription(
        key="error_state",
        name="Error State",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda x: x.error_state,
        enabled=lambda x: True,
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up MELCloud device binary sensors based on config_entry."""
    entry_config = hass.data[DOMAIN][entry.entry_id]

    mel_devices = entry_config.get(MEL_DEVICES)
    entities = []
    entities.extend(
        [
            MelDeviceBinarySensor(mel_device, description)
            for description in ATA_BINARY_SENSORS
            for mel_device in mel_devices[DEVICE_TYPE_ATA]
            if description.enabled(mel_device)
        ]
    )
    async_add_entities(entities, False)


class MelDeviceBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Binary Sensor."""

    entity_description: MelcloudBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        api: MelCloudDevice,
        description: MelcloudBinarySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(api.coordinator)
        self._api = api
        self.entity_description = description

        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-{description.key}"
        self._attr_device_info = api.device_info
        self._attr_extra_state_attributes = api.extra_attributes

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self.entity_description.value_fn(self._api)
