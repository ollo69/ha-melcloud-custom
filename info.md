# MELCloud HomeAssistant custom component
A full featured Homeassistant custom component to drive MELCloud AC devices.

This custom component is based on the native Home Assistant [MELCloud component](https://github.com/home-assistant/core/tree/dev/homeassistant/components/melcloud) released with version 0.106 and on the same underlying [PyMelCloud library](https://github.com/vilppuvuorinen/pymelcloud).

## Custom component additional features
I just added some features to the existing native components, waiting for the same features to be implemented:

1. Login password is stored in the registry during integration configuration. The access token is recreated every time the Home Assistant start and is not stored in the registry. Now you must also provide login language from a list of available options. The language should be the same that you normaly use for other MELCloud application (e.g. your phone app).

1. During integration configuration you can choose wich additional sensors you want to be created.

1. Added sensor to monitor WiFi signal.

1. Added binary sensor to monitor error state.

1. Added some attributes to the sensors to provide additional information (SerialNo, Unit Info, etc)

1. Added control for Vertical and Horizontal Swing Modes
    
## Component setup    
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

1. Reboot hpme assistant
1. Congrats! You're all set!

