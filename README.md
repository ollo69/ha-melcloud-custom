[![](https://img.shields.io/github/release/ollo69/ha-melcloud-custom/all.svg?style=for-the-badge)](https://github.com/ollo69/ha-melcloud-custom/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![](https://img.shields.io/github/license/ollo69/ha-melcloud-custom?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/badge/MAINTAINER-%40ollo69-red?style=for-the-badge)](https://github.com/ollo69)
[![](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge)](https://community.home-assistant.io)

# MELCloud HomeAssistant custom component

## ℹ️ Note
Due to the latest restrictions introduced by MELCloud platform (see [here](https://github.com/ollo69/ha-melcloud-custom/issues/13)) I decided to implement the control of my AC devices through the adoption of small and economical `ESP8266` devices connected to `CN105` units connector which allow real-time control via MQTT (see [here](https://github.com/dzungpv/mitsubishi2MQTT) an example).

As consequence I no longer have a way to maintain this integration, fixing bug, implementing new features and adapting to HA architecture changes.

If anyone is interested in taking charge of it, they can possibly fork this repository and I will report the new reference link here in the notes.

**This repository will be shortly moved in state `archived`.**

## Description
A full featured Homeassistant custom component to drive MELCloud ATA and ATW devices.

This custom component is based on the native Home Assistant [MELCloud component](https://github.com/home-assistant/core/tree/dev/homeassistant/components/melcloud) released with version 0.106 and on the same underlying [PyMelCloud library](https://github.com/vilppuvuorinen/pymelcloud).

## Custom component additional features
I just added some features to the existing native components, waiting for the same features to be implemented:

1. Add support for login language from a list of available options. The language should be the same that you normaly use for other MELCloud application (e.g. your phone app).

1. Added control for **Vertical and Horizontal Swing Modes** on ATA devices using default Swing features.

1. Added sensor to monitor WiFi signal.

1. Added binary sensor to monitor error state.

1. Added some attributes to the sensors to provide additional information (SerialNo, Unit Info, etc)

1. Implemented use of `coordinator` to have update for all entities syncronizes

## Installation & configuration
You can install this component in two ways: via HACS or manually.

### Option A: Installing via HACS
If you have HACS, you must add this repository ("https://github.com/ollo69/ha-melcloud-custom") to your Custom Repository selecting the Configuration Tab in the HACS page.
After this you can go in the Integration Tab and search the "MELCloud Custom" component to install it.

### Option B: Manually installation (custom_component)
1. Clone the git master branch.
1. Unzip/copy the melcloud_custom direcotry within the `custom_components` directory of your homeassistant installation.
The `custom_components` directory resides within your homeassistant configuration directory.
Usually, the configuration directory is within your home (`~/.homeassistant/`).
In other words, the configuration directory of homeassistant is where the configuration.yaml file is located.
After a correct installation, your configuration directory should look like the following.
    ```
    └── ...
    └── configuration.yaml
    └── secrects.yaml
    └── custom_components
        └── melcloud_custom
            └── __init__.py
            └── binary_sensor.py
            └── climate.py
            └── ...
    ```

    **Note**: if the custom_components directory does not exist, you need to create it.

### Component setup
Once the component has been installed, you need to configure it in order to make it work.
There are two ways of doing so:
- Using the web interface (Lovelace) [**recommended**]
- Manually editing the configuration.yaml file

#### Option A: Configuration using the web UI [recommended]
Simply add a new "integration" and look for "MELCloud Custom" among the proposed ones. Do not confuse with "MELCloud" that is the native one!

#### Option B: Configuration via editing configuration.yaml
Follow these steps only if the previous configuration method did not work for you.

1. Setup your MELCloud credentials. Edit/create the `secrets.yaml` file,
 which is located within the config directory as well. Add the following:

     ```
    melcloud_username: my_melcloud_email@domain.com
    melcloud_password: my_melcloud_password
    ```

    Where "my_melcloud_email@domain.com" is your MELCloud account email and "my_melcloud_password" is the associated password.

1. Enable the component by editing the configuration.yaml file (within the config directory as well).
Edit it by adding the following lines:
    ```
    melcloud_custom:
      username: !secret melcloud_username
      password: !secret melcloud_password
      language: my_melcloud_language
    ```

    Where "my_melcloud_language" is your MELCloud account language and can be one of the following (eg: EN):

        EN = English
        BG = Bulgarian
        CS = Czech
        DA = Danish
        DE = German
        ET = Estonian
        ES = Spanish
        FR = French
        HY = Armenian
        LV = Latvian
        LT = Lithuanian
        HU = Hungarian
        NL = Dutch
        NO = Norwegian
        PL = Polish
        PT = Portuguese
        RU = Russian
        FI = Finnish
        SV = Swedish
        IT = Italian
        UK = Ukrainian
        TR = Turkish
        EL = Greek
        HR = Croatian
        RO = Romanian
        SL = Slovenian

**Note!** In this case you do not need to replace "!secret melcloud_username" and "!secret melcloud_password".
Those are place holders that homeassistant automatically replaces by looking at the secrets.yaml file.

1. Reboot home assistant
1. Congrats! You're all set!

