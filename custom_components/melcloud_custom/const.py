"""Constants for the MELCloud Climate integration."""

DOMAIN = "melcloud_custom"
MEL_DEVICES = "mel_devices"

CONF_LANGUAGE = "language"

ATTR_STATUS = "status"
ATTR_VANE_VERTICAL = "vane_vertical"
ATTR_VANE_HORIZONTAL = "vane_horizontal"


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
    'EN': Language.English,
    'BG': Language.Bulgarian,
    'CS': Language.Czech,
    'DA': Language.Danish,
    'DE': Language.German,
    'ET': Language.Estonian,
    'ES': Language.Spanish,
    'FR': Language.French,
    'HY': Language.Armenian,
    'LV': Language.Latvian,
    'LT': Language.Lithuanian,
    'HU': Language.Hungarian,
    'NL': Language.Dutch,
    'NO': Language.Norwegian,
    'PL': Language.Polish,
    'PT': Language.Portuguese,
    'RU': Language.Russian,
    'FI': Language.Finnish,
    'SV': Language.Swedish,
    'IT': Language.Italian,
    'UK': Language.Ukrainian,
    'TR': Language.Turkish,
    'EL': Language.Greek,
    'HR': Language.Croatian,
    'RO': Language.Romanian,
    'SL': Language.Slovenian,
}
