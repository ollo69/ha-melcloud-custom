"""Constants for the MELCloud Climate integration."""

DOMAIN = "melcloud_custom"
MEL_DEVICES = "mel_devices"

CONF_LANGUAGE = "language"

ATTR_STATUS = "status"
ATTR_VANE_VERTICAL = "vane_vertical"
ATTR_VANE_HORIZONTAL = "vane_horizontal"

DEFAULT_SCAN_INTERVAL = 900


class HorSwingModes:
    """Horizontal swing modes names."""

    Auto = "HorizontalAuto"
    Left = "HorizontalLeft"
    MiddleLeft = "HorizontalMiddleLeft"
    Middle = "HorizontalMiddle"
    MiddleRight = "HorizontalMiddleRight"
    Right = "HorizontalRight"
    Split = "HorizontalSplit"
    Swing = "HorizontalSwing"


class VertSwingModes:
    """Vertical swing modes names."""

    Auto = "VerticalAuto"
    Top = "VerticalTop"
    MiddleTop = "VerticalMiddleTop"
    Middle = "VerticalMiddle"
    MiddleBottom = "VerticalMiddleBottom"
    Bottom = "VerticalBottom"
    Swing = "VerticalSwing"


class Language:
    """Melcloud languages."""

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
    "EN": Language.English,
    "BG": Language.Bulgarian,
    "CS": Language.Czech,
    "DA": Language.Danish,
    "DE": Language.German,
    "EL": Language.Greek,
    "ES": Language.Spanish,
    "ET": Language.Estonian,
    "FI": Language.Finnish,
    "FR": Language.French,
    "HR": Language.Croatian,
    "HU": Language.Hungarian,
    "HY": Language.Armenian,
    "IT": Language.Italian,
    "LV": Language.Latvian,
    "LT": Language.Lithuanian,
    "NL": Language.Dutch,
    "NO": Language.Norwegian,
    "PL": Language.Polish,
    "PT": Language.Portuguese,
    "RO": Language.Romanian,
    "RU": Language.Russian,
    "SL": Language.Slovenian,
    "SV": Language.Swedish,
    "TR": Language.Turkish,
    "UK": Language.Ukrainian,
}
