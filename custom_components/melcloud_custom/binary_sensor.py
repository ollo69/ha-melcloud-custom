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


async def async_setup_entry(hass, entry, async_add_entities):
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


class MelDeviceBinarySensor(BinarySensorEntity):
    """Representation of a Binary Sensor."""

    entity_description: MelcloudBinarySensorEntityDescription

    def __init__(
        self,
        api: MelCloudDevice,
        description: MelcloudBinarySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self._api = api
        self.entity_description = description

        self._attr_name = f"{api.name} {description.name}"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-{description.key}"

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self.entity_description.value_fn(self._api)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""
        return self._api.extra_attributes

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()
