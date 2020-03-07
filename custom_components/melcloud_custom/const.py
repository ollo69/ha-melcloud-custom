"""Constants for the MELCloud Climate integration."""
import pymelcloud.ata_device as ata_device
from pymelcloud.const import UNIT_TEMP_CELSIUS, UNIT_TEMP_FAHRENHEIT

from homeassistant.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
)
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT

DOMAIN = "melcloud_custom"
CONF_LANGUAGE = "language"
MEL_DEVICES = "mel_devices"
WIFI_SIGNAL = "wifi_signal"
ROOM_TEMPERATURE = "room_temperature"
ENERGY = "energy"
ERROR_STATE = "error_state"

ATTR_VANE_VERTICAL = "vane_vertical"
ATTR_VANE_HORIZONTAL = "vane_horizontal"

class Language:
    English = 0
    Bulgarian = 1
    Czech = 2
    Danish = 3
    German = 4
    Estonian = 5
    Spanish = 6
    French = 7
    Armenian = 8
    Latvian = 9
    Lithuanian = 10
    Hungarian = 11
    Dutch = 12
    Norwegian = 13
    Polish = 14
    Portuguese = 15
    Russian = 16
    Finnish = 17
    Swedish = 18
    Italian = 19
    Ukrainian = 20
    Turkish = 21
    Greek = 22
    Croatian = 23
    Romanian = 24
    Slovenian = 25

LANGUAGES = {
    'EN' : Language.English,
    'BG' : Language.Bulgarian,
    'CS' : Language.Czech,
    'DA' : Language.Danish,
    'DE' : Language.German,
    'ET' : Language.Estonian,
    'ES' : Language.Spanish,
    'FR' : Language.French,
    'HY' : Language.Armenian,
    'LV' : Language.Latvian,
    'LT' : Language.Lithuanian,
    'HU' : Language.Hungarian,
    'NL' : Language.Dutch,
    'NO' : Language.Norwegian,
    'PL' : Language.Polish,
    'PT' : Language.Portuguese,
    'RU' : Language.Russian,
    'FI' : Language.Finnish,
    'SV' : Language.Swedish,
    'IT' : Language.Italian,
    'UK' : Language.Ukrainian,
    'TR' : Language.Turkish,
    'EL' : Language.Greek,
    'HR' : Language.Croatian,
    'RO' : Language.Romanian,
    'SL' : Language.Slovenian,
}

class VertSwingModes:
    Auto = 'VerticalAuto' 
    Top = 'VerticalTop'
    MiddleTop = 'VerticalMiddleTop' 
    Middle = 'VerticalMiddle'
    MiddleBottom = 'VerticalMiddleBottom' 
    Bottom = 'VerticalBottom'
    Swing = 'VerticalSwing'

class HorSwingModes:
    Auto = 'HorizontalAuto' 
    Left = 'HorizontalLeft'
    MiddleLeft = 'HorizontalMiddleLeft' 
    Middle = 'HorizontalMiddle'
    MiddleRight = 'HorizontalMiddleRight' 
    Right = 'HorizontalRight'
    Split = 'HorizontalSplit'
    Swing = 'HorizontalSwing'

HVAC_MODE_LOOKUP = {
    ata_device.OPERATION_MODE_HEAT: HVAC_MODE_HEAT,
    ata_device.OPERATION_MODE_DRY: HVAC_MODE_DRY,
    ata_device.OPERATION_MODE_COOL: HVAC_MODE_COOL,
    ata_device.OPERATION_MODE_FAN_ONLY: HVAC_MODE_FAN_ONLY,
    ata_device.OPERATION_MODE_HEAT_COOL: HVAC_MODE_HEAT_COOL,
}
HVAC_MODE_REVERSE_LOOKUP = {v: k for k, v in HVAC_MODE_LOOKUP.items()}

HVAC_VVANE_LOOKUP = {
    ata_device.V_VANE_POSITION_AUTO: VertSwingModes.Auto,
    ata_device.V_VANE_POSITION_1: VertSwingModes.Top,
    ata_device.V_VANE_POSITION_2: VertSwingModes.MiddleTop,
    ata_device.V_VANE_POSITION_3: VertSwingModes.Middle,
    ata_device.V_VANE_POSITION_4: VertSwingModes.MiddleBottom,
    ata_device.V_VANE_POSITION_5: VertSwingModes.Bottom,
    ata_device.V_VANE_POSITION_SWING: VertSwingModes.Swing,
    #ata_device.V_VANE_POSITION_UNDEFINED: "undefined",
}
HVAC_VVANE_REVERSE_LOOKUP = {v: k for k, v in HVAC_VVANE_LOOKUP.items()}

HVAC_HVANE_LOOKUP = {
    ata_device.H_VANE_POSITION_AUTO: HorSwingModes.Auto,
    ata_device.H_VANE_POSITION_1: HorSwingModes.Left,
    ata_device.H_VANE_POSITION_2: HorSwingModes.MiddleLeft,
    ata_device.H_VANE_POSITION_3: HorSwingModes.Middle,
    ata_device.H_VANE_POSITION_4: HorSwingModes.MiddleRight,
    ata_device.H_VANE_POSITION_5: HorSwingModes.Right,
    ata_device.H_VANE_POSITION_SPLIT: HorSwingModes.Split,
    ata_device.H_VANE_POSITION_SWING: HorSwingModes.Swing,
    #ata_device.V_VANE_POSITION_UNDEFINED: "undefined",
}
HVAC_HVANE_REVERSE_LOOKUP = {v: k for k, v in HVAC_HVANE_LOOKUP.items()}

TEMP_UNIT_LOOKUP = {
    UNIT_TEMP_CELSIUS: TEMP_CELSIUS,
    UNIT_TEMP_FAHRENHEIT: TEMP_FAHRENHEIT,
}
TEMP_UNIT_REVERSE_LOOKUP = {v: k for k, v in TEMP_UNIT_LOOKUP.items()}
