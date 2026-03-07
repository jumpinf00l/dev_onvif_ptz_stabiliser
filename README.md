# ONVIF PTZ Helper
A lightweight Home Assistant App (formerly Add-On) to help PTZ cameras which don't reliably report or update their 'PanTilt' and 'Zoom' status, such as continuing to report "Moving" when the camera is not actually moving and not reporting "Idle". It detects changes in the PTZ coordinates and automatically sends a 'Stop' command once the camera stabilises, which ensures that the camera updates the 'PanTilt' and 'Zoom' statuses to "Idle".

This Home Assistant App was specifically developed to assist with adding [Frigate Autotracking](https://docs.frigate.video/configuration/autotracking/) to unsupported cameras [such as the ones tested below](#tested-camera-models), but it may help with other applications or services which rely on reliable 'PanTilt' and 'Zoom' statuses.

## 🚀 Features
- <b>Lightweight:</b> Consumes bugger all system resources on the Home Assistant host.
- <b>Multi-Camera Support:</b> Monitors multiple cameras simultaneously with different interval and history configurations using threading.
- <b>Adaptive Polling:</b> Switches between idle and active polling intervals to save CPU and network bandwidth.
- <b>Home Assistant Ready:</b> Designed to deploy as a Home Assistant App (you're running Frigate in Home Assistant, right?).
- <b>Robust Connectivity:</b> Automatic reconnection logic with configurable backoff.
- <b>Standalone:</b> Talks directly to the camera and doesn't require plug-ins or additional configuration in applications or services like Frigate.

## 💡 Inspired By / Attribution:
ONVIF PTZ Helper was developed with the following attributions in mind:<br>
<br>
[Frigate NVR™ - Realtime Object Detection for IP Cameras](https://github.com/blakeblackshear/frigate)<br>
ONVIF PTZ Helper seeks to extend the support of Frigate to allow Autotracking to be configured for unsupported PTZ cameras.<br>
<br>
[Zeep: Python SOAP client](https://github.com/mvantellingen/python-zeep)<br>
ONVIF PTZ Helper uses the Python Zeep library for SOAP connections to the camera.<br>
<br>
[python-onvif-zeep](https://github.com/FalkTannhaeuser/python-onvif-zeep)<br>
ONVIF PTZ Helper uses the Python ONVIF Zeep library to interface with the camera's Media and PTZ services.<br>
<br>
[Open Network Video Interface Forum (ONVIF)](https://onvif.org)<br>
ONVIF PTZ Helper uses ONVIF which is an industry standard set of interfaces (e.g. using SOAP and XML) which is administered by the Open Network Video Interface Forum.<br>

## ✅ Tested Camera Models<a name="tested-camera-models"></a>
The below camera makes and models have been tested with Frigate Autotracking.
| Brand | Model | Working Status | idle_polling_interval | active_polling_interval | active_polling_history | Notes |
| ----- | ----- | -------------- | --------------------- | ----------------------- | ---------------------- | ----- |
| Hikvision | DS-2DE4A425IW-DE | ✅ Working  | 0.5 | 0.2 | 3 | - Untested with zooming |
| Hikvision | DS-2DE2A404IW-DE3 | ⚠️ Working (see note) | 0.5 | 0.3 | 3 | - Untested with zooming <br>- mechanical PTZ movement is slow and may lose subjects more easily |

## 🛠 Installation
1. Add the app repository to your Home Assistant App Store (click the 'Add' button):

[![Open your Home Assistant instance and show the add app repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fjumpinf00l%2Fdev_onvif_ptz_stabiliser)

2. Install the app from your Home Assistant App Store:

[![Open your Home Assistant instance and show the dashboard of an app.](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=896fce98_onvif_ptz_helper&repository_url=https%3A%2F%2Fgithub.com%2Fjumpinf00l%2Fdev_onvif_ptz_stabiliser)

3. Configure the options via the Configuration tab (see [Configuration](#configuration))

## ℹ️ General Notes
The following notes apply in all cases.
- Don't use your camera's admin account, a dedicated camera account for ONVIF PTZ Helper is recommended for security. Configure only the essential security roles/permissions required to allow ONVIF PTZ Helper to log into and control PTZ - video streaming is specifically not used and not required.
- You may need to enable the ONVIF interface or configure a separate ONVIF account in your camera's configuration. See the manufacturer's documentation for further information.
- Avoid overloading your camera's CPU with unnecessarily short polling intervals, especially once PTZ movement is detected when CPU usage is most likely at its highest. Most cameras will take around 0.5 - 1 second to move to any position, so polling intervals that are short enough to detect PTZ movement starting and stopping in a timely fashion are all that is needed.

## 🦅 Frigate Notes
The following notes are specific to Frigate Autotracking, but may apply to other applications or services.
- It may take several attempts for Frigate Autotracking calibration to complete successfully. Watch the log output of your Frigate App/container to see the calibration progresson and watch for calibration failures.
- Set ONFIV PTZ Helper's polling intervals and history configuration conservatively (around 0.5 sec) at first to account for slower camera motors, then progressively to try to reduce the idle and active intervals to tune the best performance for your camera. Run Frigate Autotracking calibration each time by removing the `movement_weights` dictionary from your configuration and setting `calibrate_on_startup` to true (see [Frigate Camera Autotracking](https://docs.frigate.video/configuration/autotracking/)).
- Retry Autotracking calibration with your desired configuration 2-3 times before changing your configuration since it may fail the first time but succeed following times with no changes.
> [!CAUTION]
> <b>The Frigate web service will not run during Autotracking calibration (see [Frigate Camera Autotracking > Calibration](https://docs.frigate.video/configuration/autotracking/#calibration))</b>.<br>This is normal and prevents other Frigate services from interrupting the Autotracking calibration. This is not a result of ONVIF PTZ Helper, and the web service will start once calibration is complete which may take several minutes. If there are no Autotracking progress updates in the Frigate App/container logs console after the initial update, check your ONVIF PTZ Helper configuration and log output to confirm that it is able to connect to the camera and poll its 'PanTilt' and 'Zoom' correctly (try 'DEBUG' logging).

## ⚙️ Configuration<a name="configuration"></a>
### Configuration options
The ONVIF PTZ Helper Home Assistant App accepts the below configuration:

| Option | Sub-option | YAML option | Description | Type | Required | Example | Default |
| ------ | ---------- | ----------- | ----------- | ---- | -------- |-------- | ------- |
| Log level | | ```log_level``` | Verbosity to use in logging <br><i>Note:</i> 'INFO' is recommended, 'DEBUG' will consume system resources and should only be used temporarily for debugging | String | True | INFO | INFO |
| Cameras | | ```cameras``` | List of ONVIF cameras to monitor | Dictionary | | | |
| | Camera Name | ```camera_name``` | A friendly camera name for configuration and logging | String | True | Driveway PTZ | |
| | Hostname/IP Address | ```host``` | The hostname or IP address of the camera | String | True | 10.0.0.123 | |
| | Port | ```port``` | The ONVIF interface port number of the camera | Integer | True | 80 | |
| | Ignore SSL | ```ignore_ssl``` | Ignore SSL certificate validation errors | Boolean | False | True | False
| | Username | ```username``` | The username to log into the ONVIF interface of the camera | String | True | onvif_user | |
| | Password | ```password``` | The password to log into the ONVIF interface of the camera | String | True | \<a secure password> | |
| | Reconnect time | ```reconnect_time``` | Seconds to wait after a disconnection before attempting to reconnect (minimum 0) | Float | False | 30 | 5 |
| | Idle Polling Inverval (seconds) | ```idle_polling_interval``` | Seconds to wait between polls while PTZ movement is idle (minimum: 0) | Float | False | 0.5 | 0.3 |
| | Active Polling Interval (seconds) | ```active_polling_interval``` | Seconds to wait between polls while PTZ movement is idle (minimum: 0) | Float | False | 0.1 | 0.3 |
| | Active Polling History | ```active_polling_history``` | The number of active polls with identical PTZ coordinates to determine that PTZ movement has stopped, includes the current poll (minimum: 2) | Integer | False | 3 | 2 |

### Example YAML configuration
```yaml
log_level: INFO
cameras:
  - camera_name: Driveway PTZ
    host: 10.0.0.123
    port: 80
    username: onvif
    password: ####
    idle_polling_interval: 0.5
    active_polling_interval: 0.2
    active_polling_history: 3
  - camera_name: Front PTZ
    host: 10.0.0.124
    port: 8976
    ignore_ssl: true
    username: onvif
    password: ####
    reconnect_time: 30
    idle_polling_interval: 0.5
    active_polling_interval: 0.3
    active_polling_history: 3
```

## ❔ Frequently Asked Questions
<b>Q:</b> ONVIF polling seems inefficient, why not subscribe to PTZ coordinate updates?<br>
<b>A:</b> It's kind of the whole reason we're here - if the camera doesn't fully comply with the ONVIF standard and doesn't reliably update its PanTilt and Zoom statuses, then it likely doesn't support subscriptions to PTZ coordinate updates. The two Hikvision cameras which were tested during development definitely do not support subscribing to PTZ coordinate updates.<br>

<b>Q:</b> Can I run this in a Docker container outside of Home Assistant?<br>
<b>A:</b> There are handlers for passing the configuration during the Docker build process, but this currently only supports a single camera and is very, very untested. You could try mapping an options.json to /data/options.json. Why not Home Assistant?<br>

<b>Q:</b> Can I submit working cameras to the Tested Camera Models list?<br>
<b>A:</b> Sure, raise a PR or submit an issue. <br>

<b>Q:</b> Why is my <i>\<insert thing></i> doing <i>\<insert problem></i> since I configured ONVIF PTZ Helper?<br>
<b>A:</b> Sorry, this is open-source software with no support, warranty, liability, etc. Please try to resolve the issue yourself, then document the issue and resolution and raise a PR or submit an issue.

## ⚖️ The Necessary Disclaimer:
Please read this carefully before using this software.

1. No Affiliation
ONVIF PTZ Helper is an independent open-source utility. Neither it nor its authors are affiliated with, authorised, maintained, sponsored, or endorsed by Frigate NVR™, Open Network Video Interface Forum (ONVIF), or any related camera manufacturer (e.g. Hikvision, Dahua, etc.). All product and company names are the registered trademarks of their original owners.
2. "As-Is" Software
This software is provided "as-is" and "as-available," without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement.
3. Assumption of Risk
By using this software, you acknowledge that you should consider:
   - Network Requirements: Frequent PTZ communication increases network traffic.
   - Security: You should take appropriate measures to ensure and maintain all aspects of security such as your network, camera management interfaces, and video streaming.
   - Liability: In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.
