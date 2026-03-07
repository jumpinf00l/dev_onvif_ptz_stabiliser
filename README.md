#ONVIF PTZ Helper
A lightweight Python service designed to monitor ONVIF-compliant PTZ (Pan-Tilt-Zoom) cameras. It detects movement and automatically sends a Stop command once the camera stabilizes, preventing "runaway" PTZ or ensuring the camera is fully idle after manual or automated adjustments.

## 🚀 Features
Multi-Camera Support: Monitors multiple cameras simultaneously using Python threading.
Adaptive Polling: Switches between idle and active polling intervals to save CPU and network bandwidth.
Home Assistant Ready: Native support for /data/options.json and map_timezone.
Robust Connectivity: Automatic reconnection logic with configurable backoff.

## 🛠 Installation
### As a Home Assistant App
1. Add the app repository to your Home Assistant App Store (click the 'Add' button):

[![Open your Home Assistant instance and show the add app repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fjumpinf00l%2Fdev_onvif_ptz_stabiliser)

2. Install the app from your Home Assistant App Store:

[![Open your Home Assistant instance and show the dashboard of an app.](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=896fce98_onvif_ptz_helper&repository_url=https%3A%2F%2Fgithub.com%2Fjumpinf00l%2Fdev_onvif_ptz_stabiliser)

3. Configure the settings via the Configuration tab

### Via Docker
Build the image using the provided Dockerfile, which utilizes a Python Virtual Environment (venv) for security and stability:Bashdocker build -t onvif-ptz-helper.

```bash
docker run -d \
  -e LOG_LEVEL="INFO" \
  -e CAMERA_NAME="Front Door" \
  -e host="192.168.1.50" \
  -e PORT="80" \
  -e USERNAME="admin" \
  -e PASSWORD="password123" \
  onvif-ptz-helper
```

## ⚙️ Configuration
The application accepts the below configuration:

| Key | Description | Example | Default |
| --- | ----------- | ------- | ------- |
| LOG_LEVEL | Verbosity to use in logging. INFO is recommended, DEBUG will consume system resources and should only be used temporarily for debugging (Default: INFO). | INFO | INFO |
