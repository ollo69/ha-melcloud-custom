"""Platform for water_heater integration."""
from __future__ import annotations

from typing import Any

from pymelcloud import DEVICE_TYPE_ATW, AtwDevice
from pymelcloud.atw_device import (
    PROPERTY_OPERATION_MODE,
    PROPERTY_TARGET_TANK_TEMPERATURE,
)
from pymelcloud.device import PROPERTY_POWER

from homeassistant.components.water_heater import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, MelCloudDevice
from .const import ATTR_STATUS, MEL_DEVICES


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up MelCloud device climate based on config_entry."""
    mel_devices = hass.data[DOMAIN][entry.entry_id].get(MEL_DEVICES)
    async_add_entities(
        [
            AtwWaterHeater(mel_device, mel_device.device)
            for mel_device in mel_devices[DEVICE_TYPE_ATW]
        ],
        True,
    )


class AtwWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    """Air-to-Water water heater."""

    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize water heater device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_unique_id = f"{device.serial}-WH"
        self._attr_device_info = api.device_info

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self._api.async_set({PROPERTY_POWER: True})

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self._api.async_set({PROPERTY_POWER: False})

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes with device specific additions."""
        data = {ATTR_STATUS: self._device.status}
        return data

    @property
    def current_operation(self) -> str | None:
        """Return current operation as reported by pymelcloud."""
        return self._device.operation_mode

    @property
    def operation_list(self) -> list[str]:
        """Return the list of available operation modes as reported by pymelcloud."""
        return self._device.operation_modes

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._device.tank_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device.target_tank_temperature

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        await self._api.async_set(
            {
                PROPERTY_TARGET_TANK_TEMPERATURE: kwargs.get(
                    "temperature", self.target_temperature
                )
            }
        )

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        await self._api.async_set({PROPERTY_OPERATION_MODE: operation_mode})

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self._device.target_tank_temperature_min or DEFAULT_MIN_TEMP

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self._device.target_tank_temperature_max or DEFAULT_MAX_TEMP
