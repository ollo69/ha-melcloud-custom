"""Platform for climate integration."""
from __future__ import annotations

from typing import Any

from pymelcloud import DEVICE_TYPE_ATA, DEVICE_TYPE_ATW, AtaDevice, AtwDevice
import pymelcloud.ata_device as ata
import pymelcloud.atw_device as atw
from pymelcloud.atw_device import (
    PROPERTY_ZONE_1_OPERATION_MODE,
    PROPERTY_ZONE_2_OPERATION_MODE,
    Zone,
)
from pymelcloud.device import PROPERTY_POWER

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MelCloudDevice
from .const import (
    ATTR_STATUS,
    ATTR_VANE_HORIZONTAL,
    ATTR_VANE_VERTICAL,
    DOMAIN,
    MEL_DEVICES,
    HorSwingModes,
    VertSwingModes,
)


ATA_HVAC_MODE_LOOKUP: dict[str, HVACMode] = {
    ata.OPERATION_MODE_HEAT: HVACMode.HEAT,
    ata.OPERATION_MODE_DRY: HVACMode.DRY,
    ata.OPERATION_MODE_COOL: HVACMode.COOL,
    ata.OPERATION_MODE_FAN_ONLY: HVACMode.FAN_ONLY,
    ata.OPERATION_MODE_HEAT_COOL: HVACMode.HEAT_COOL,
}
ATA_HVAC_MODE_REVERSE_LOOKUP: dict[HVACMode, str] = {
    v: k for k, v in ATA_HVAC_MODE_LOOKUP.items()
}


ATA_HVAC_VVANE_LOOKUP: dict[str, str] = {
    ata.V_VANE_POSITION_AUTO: VertSwingModes.Auto,
    ata.V_VANE_POSITION_1: VertSwingModes.Top,
    ata.V_VANE_POSITION_2: VertSwingModes.MiddleTop,
    ata.V_VANE_POSITION_3: VertSwingModes.Middle,
    ata.V_VANE_POSITION_4: VertSwingModes.MiddleBottom,
    ata.V_VANE_POSITION_5: VertSwingModes.Bottom,
    ata.V_VANE_POSITION_SWING: VertSwingModes.Swing,
}
ATA_HVAC_VVANE_REVERSE_LOOKUP: dict[str, str] = {
    v: k for k, v in ATA_HVAC_VVANE_LOOKUP.items()
}


ATA_HVAC_HVANE_LOOKUP: dict[str, str] = {
    ata.H_VANE_POSITION_AUTO: HorSwingModes.Auto,
    ata.H_VANE_POSITION_1: HorSwingModes.Left,
    ata.H_VANE_POSITION_2: HorSwingModes.MiddleLeft,
    ata.H_VANE_POSITION_3: HorSwingModes.Middle,
    ata.H_VANE_POSITION_4: HorSwingModes.MiddleRight,
    ata.H_VANE_POSITION_5: HorSwingModes.Right,
    ata.H_VANE_POSITION_SPLIT: HorSwingModes.Split,
    ata.H_VANE_POSITION_SWING: HorSwingModes.Swing,
}
ATA_HVAC_HVANE_REVERSE_LOOKUP: dict[str, str] = {
    v: k for k, v in ATA_HVAC_HVANE_LOOKUP.items()
}


ATW_ZONE_HVAC_MODE_LOOKUP: dict[str, HVACMode] = {
    atw.ZONE_OPERATION_MODE_HEAT: HVACMode.HEAT,
    atw.ZONE_OPERATION_MODE_COOL: HVACMode.COOL,
}
ATW_ZONE_HVAC_MODE_REVERSE_LOOKUP: dict[HVACMode, str] = {
    v: k for k, v in ATW_ZONE_HVAC_MODE_LOOKUP.items()
}


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
):
    """Set up MelCloud device climate based on config_entry."""
    mel_devices = hass.data[DOMAIN][entry.entry_id].get(MEL_DEVICES)
    entities = []
    entities.extend(
        [
            AtaDeviceClimate(mel_device, mel_device.device)
            for mel_device in mel_devices[DEVICE_TYPE_ATA]
        ]
    )
    entities.extend(
        [
            AtwDeviceZoneClimate(mel_device, mel_device.device, zone)
            for mel_device in mel_devices[DEVICE_TYPE_ATW]
            for zone in mel_device.device.zones
        ]
    )
    async_add_entities(entities, True)


class MelCloudClimate(CoordinatorEntity, ClimateEntity):
    """Base climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, device: MelCloudDevice):
        """Initialize the climate."""
        super().__init__(device.coordinator)
        self.api = device
        self._base_device = self.api.device

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self.api.device_info

    @property
    def target_temperature_step(self) -> float | None:
        """Return the supported step of target temperature."""
        return self._base_device.temperature_increment


class AtaDeviceClimate(MelCloudClimate):
    """Air-to-Air climate device."""

    def __init__(self, device: MelCloudDevice, ata_device: AtaDevice):
        """Initialize the climate."""
        super().__init__(device)
        self._device = ata_device
        self._attr_name = device.name
        self._attr_unique_id = f"{ata_device.serial}-{ata_device.mac}"

        self._support_ver_swing = len(self._device.vane_vertical_positions) > 0
        self._support_hor_swing = len(self._device.vane_horizontal_positions) > 0
        self._set_hor_swing = self._support_hor_swing and not self._support_ver_swing

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the optional state attributes with device specific additions."""
        attr = {}

        vane_horizontal = self._device.vane_horizontal
        if vane_horizontal:
            attr.update(
                {ATTR_VANE_HORIZONTAL: ATA_HVAC_HVANE_LOOKUP.get(vane_horizontal, None)}
            )

        vane_vertical = self._device.vane_vertical
        if vane_vertical:
            attr.update(
                {ATTR_VANE_VERTICAL: ATA_HVAC_VVANE_LOOKUP.get(vane_vertical, None)}
            )
        return attr

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        op_mode = self._device.operation_mode
        if not self._device.power or op_mode is None:
            return HVACMode.OFF
        return ATA_HVAC_MODE_LOOKUP.get(op_mode, HVACMode.AUTO)

    def _apply_set_hvac_mode(
        self, hvac_mode: HVACMode, set_dict: dict[str, Any]
    ) -> None:
        """Apply hvac mode changes to a dict used to call _device.set."""
        if hvac_mode == HVACMode.OFF:
            set_dict[PROPERTY_POWER] = False
            return

        operation_mode = ATA_HVAC_MODE_REVERSE_LOOKUP.get(hvac_mode)
        if operation_mode is None:
            raise ValueError(f"Invalid hvac_mode [{hvac_mode}]")

        set_dict[ata.PROPERTY_OPERATION_MODE] = operation_mode
        if self.hvac_mode == HVACMode.OFF:
            set_dict[PROPERTY_POWER] = True

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        set_dict = {}
        self._apply_set_hvac_mode(hvac_mode, set_dict)
        await self.api.async_set(set_dict)

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return [HVACMode.OFF] + [
            ATA_HVAC_MODE_LOOKUP.get(mode) for mode in self._device.operation_modes
        ]

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._device.room_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._device.target_temperature

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        set_dict = {}
        if hvac_mode := kwargs.get(ATTR_HVAC_MODE):
            self._apply_set_hvac_mode(HVACMode(hvac_mode), set_dict)

        if new_temp := kwargs.get(ATTR_TEMPERATURE):
            set_dict[ata.PROPERTY_TARGET_TEMPERATURE] = new_temp

        if set_dict:
            await self.api.async_set(set_dict)

    @property
    def fan_mode(self) -> str | None:
        """Return the fan setting."""
        return self._device.fan_speed

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self.api.async_set({ata.PROPERTY_FAN_SPEED: fan_mode})

    @property
    def fan_modes(self) -> list[str] | None:
        """Return the list of available fan modes."""
        return self._device.fan_speeds

    @property
    def swing_mode(self) -> str | None:
        """Return the swing mode setting."""
        swing = None
        if self._set_hor_swing and self._support_hor_swing:
            mode = self._device.vane_horizontal
            if mode is not None:
                swing = ATA_HVAC_HVANE_LOOKUP.get(mode)
        elif self._support_ver_swing:
            mode = self._device.vane_vertical
            if mode is not None:
                swing = ATA_HVAC_VVANE_LOOKUP.get(mode)

        if swing is None:
            return "Auto"

        return swing

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing mode."""
        is_hor_swing = False
        operation_mode = ATA_HVAC_VVANE_REVERSE_LOOKUP.get(swing_mode)
        if operation_mode is None:
            operation_mode = ATA_HVAC_HVANE_REVERSE_LOOKUP.get(swing_mode)
            if operation_mode is None:
                raise ValueError(f"Invalid swing_mode [{swing_mode}].")

            is_hor_swing = True
            curr_mode = self._device.vane_horizontal
            valid_swing_modes = self._device.vane_horizontal_positions
            props = {ata.PROPERTY_VANE_HORIZONTAL: operation_mode}
        else:
            curr_mode = self._device.vane_vertical
            valid_swing_modes = self._device.vane_vertical_positions
            props = {ata.PROPERTY_VANE_VERTICAL: operation_mode}

        if operation_mode not in valid_swing_modes:
            raise ValueError(f"Invalid swing_mode [{swing_mode}].")

        self._set_hor_swing = is_hor_swing
        if curr_mode != operation_mode:
            await self.api.async_set(props)

    @property
    def swing_modes(self) -> list[str] | None:
        """Return the list of available swing modes."""
        list_modes = [
            ATA_HVAC_VVANE_LOOKUP.get(mode)
            for mode in self._device.vane_vertical_positions
        ]
        for mode in self._device.vane_horizontal_positions:
            list_modes.append(ATA_HVAC_HVANE_LOOKUP.get(mode))

        return list_modes

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self.api.async_set({PROPERTY_POWER: True})

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self.api.async_set({PROPERTY_POWER: False})

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supp_feature = (
            ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TARGET_TEMPERATURE
        )
        if self._support_ver_swing or self._support_hor_swing:
            supp_feature |= ClimateEntityFeature.SWING_MODE

        return supp_feature

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        min_value = self._device.target_temperature_min
        if min_value is not None:
            return min_value

        return DEFAULT_MIN_TEMP

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        max_value = self._device.target_temperature_max
        if max_value is not None:
            return max_value

        return DEFAULT_MAX_TEMP


class AtwDeviceZoneClimate(MelCloudClimate):
    """Air-to-Water zone climate device."""

    _attr_max_temp = 30
    _attr_min_temp = 10
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(self, device: MelCloudDevice, atw_device: AtwDevice, atw_zone: Zone):
        """Initialize the climate."""
        super().__init__(device)
        self._device = atw_device
        self._zone = atw_zone
        self._attr_name = f"{device.name} {atw_zone.name}"
        self._attr_unique_id = f"{atw_device.serial}-{atw_zone.zone_index}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes with device specific additions."""
        data = {
            ATTR_STATUS: ATW_ZONE_HVAC_MODE_LOOKUP.get(
                self._zone.status, self._zone.status
            )
        }
        return data

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        mode = self._zone.operation_mode
        if not self._device.power or mode is None:
            return HVACMode.OFF
        return ATW_ZONE_HVAC_MODE_LOOKUP.get(mode, HVACMode.OFF)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.api.async_set({"power": False})
            return

        operation_mode = ATW_ZONE_HVAC_MODE_REVERSE_LOOKUP.get(hvac_mode)
        if operation_mode is None:
            raise ValueError(f"Invalid hvac_mode [{hvac_mode}]")

        if self._zone.zone_index == 1:
            props = {PROPERTY_ZONE_1_OPERATION_MODE: operation_mode}
        else:
            props = {PROPERTY_ZONE_2_OPERATION_MODE: operation_mode}
        if self.hvac_mode == HVACMode.OFF:
            props["power"] = True
        await self.api.async_set(props)

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return [self.hvac_mode]

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._zone.room_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._zone.target_temperature

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        await self._zone.set_target_temperature(
            kwargs.get("temperature", self.target_temperature)
        )
