# OctoLight
A simple plugin that adds a button to the navigation bar for toggleing a light via command line on the Raspberry Pi.

![WebUI interface](img/screenshoot.png)

## Setup
Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

	https://github.com/dominoxp/OctoLight/archive/master.zip

## Configuration
![Settings panel](img/settings.png)

Curently, you can configure settings:
- `On Command`: The System command to turn the light on
- `Off Command`: The System command to turn the light off
- `Status Command`: The System command to check current status, Exit Code 0 = off, otherwise on

- `Setup Delay Turn off time`: This sets a time out for when the light will automatically turn its self off in an event
    - Default value: 5
    - Note: This value is in minutes

- `Setup Printer Events`: This allows you to select what you would like the light to do on a printer event
    - Default is nothing
    - Set the light to do nothing, turn on, turn off, or turn on then turn itself off after the delay time value


## API
Base API URL : `GET http://YOUR_OCTOPRINT_SERVER/api/plugin/octolight?action=ACTION_NAME`

This API always returns updated light state in JSON: `{state: true}`

_(if the action parameter not given, the action toggle will be used by default)_
#### Actions
- **toggle** (default action): Toggle light switch on/off.
- **turnOn**: Turn on light.
- **turnOff**: Turn off light.
- **getState**: Get current light switch state.
- **delayOff**: Turn on light and setup timer to shutoff light after delay time, note, `&delay=VALUE` can be added to the URL to override the default time value
- **delayOffStop**: Testing for shutting off timer and light

