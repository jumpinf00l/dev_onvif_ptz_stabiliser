import time
import sys
import threading
import json
import os
from datetime import datetime
import onvif
import zeep
from zeep.transports import Transport
import requests
from typing import Optional, Dict

class ONVIFMonitorApp:
    LEVELS = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}

    def __init__(self, camera_config: Dict, min_level: str = 'INFO'):
        self.camera_name = camera_config['camera_name']
        self.host = camera_config['host']
        self.port = camera_config['port']
        self.user = camera_config['username']
        self.password = camera_config['password']
        self.ignore_ssl = camera_config.get('ignore_ssl', False)
        self.reconnect_time = camera_config.get('reconnect_time', 5)
        self.polling_interval = camera_config.get('polling_interval', 0.3)
        self.fast_poll_on_move = camera_config.get('fast_poll_on_move', True)
        
        self.min_level_value = self.LEVELS.get(min_level.upper(), 1)
        self.cam: Optional[onvif.ONVIFCamera] = None
        self.ptz_service = None
        self.media_service = None
        self.token = None
        self.prev_pan = None
        self.prev_tilt = None
        self.prev_zoom = None
        self.is_currently_moving = False

    def log(self, message: str, level: str = 'INFO'):
        lvl_upper = level.upper()
        if self.LEVELS.get(lvl_upper, 1) < self.min_level_value:
            return
        severity_char = lvl_upper[0]
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"{now} - [{severity_char}] - [{self.camera_name}] - {message}")

    def connect(self):
        while True:
            try:
                self.log(f"Connecting to '{self.camera_name}': {self.host}:{self.port}...", "INFO")
                transport = None
                if self.ignore_ssl:
                    session = requests.Session()
                    session.verify = False
                    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
                    transport = Transport(session=session)
                self.cam = onvif.ONVIFCamera(self.host, self.port, self.user, self.password, transport=transport)
                self.media_service = self.cam.create_media_service()
                self.ptz_service = self.cam.create_ptz_service()
                profiles = self.media_service.GetProfiles()
                if not profiles:
                    raise Exception("No ONVIF media service profiles found, cannot get PTZ token")
                self.token = profiles[0].token
                status = self.ptz_service.GetStatus({'ProfileToken': self.token})
                self.prev_pan = status.Position.PanTilt.x
                self.prev_tilt = status.Position.PanTilt.y
                self.prev_zoom = status.Position.Zoom.x
                self.log(f"Connected to '{self.camera_name}': {self.host}:{self.port}", "INFO")
                return True
            except Exception as e:
                self.log(f"Connection failed: {e}", "CRITICAL")
                self.log(f"Reattempting in {self.reconnect_time}s...", "INFO")
                time.sleep(self.reconnect_time)

    def send_stop_command(self):
        try:
            self.log("Sending stop command", "INFO")
            self.ptz_service.Stop({'ProfileToken': self.token, 'PanTilt': True, 'Zoom': True})
            self.log("Stop command sent", "INFO")
        except Exception as e:
            self.log(f"Stop command failed: {e}", "ERROR")

    def run(self):
        self.log("Monitoring PTZ position...", "INFO")
        while True:
            try:
                status = self.ptz_service.GetStatus({'ProfileToken': self.token})
                curr_pan = status.Position.PanTilt.x
                curr_tilt = status.Position.PanTilt.y
                curr_zoom = status.Position.Zoom.x
                curr_pantiltstatus = status.MoveStatus.PanTilt
                curr_zoomstatus = status.MoveStatus.PanTilt
                is_pt_moving = curr_pantiltstatus == 'MOVING'
                is_zoom_moving = curr_zoomstatus == 'MOVING'
                position_changed = (curr_pan != self.prev_pan or curr_tilt != self.prev_tilt or curr_zoom != self.prev_zoom)
                currently_moving = position_changed or is_pt_moving or is_zoom_moving
                
                self.log(f"PTZ position: P:{curr_pan:.4f} T:{curr_tilt:.4f} Z:{curr_zoom:.4f}", "DEBUG")
                self.log(f"PTZ position changing: {currently_moving}", "DEBUG")
                self.log(f"PTZ status: PanTilt: {curr_pantiltstatus}, Zoom: {curr_zoomstatus}", "DEBUG")

                if currently_moving:
                    if not self.is_currently_moving:
                        self.log("Movement detected, waiting for PTZ position to stabilise...", "INFO")
                        self.is_currently_moving = True
                    if not self.fast_poll_on_move:
                        time.sleep(self.polling_interval)
                else:
                    if self.is_currently_moving:
                        self.log("PTZ position stabilised while PTZ status still 'MOVING'", "INFO")
                        self.send_stop_command()
                        self.is_currently_moving = False
                        self.log("Monitoring PTZ position...", "INFO")
                    time.sleep(self.polling_interval)
                
                self.prev_pan = curr_pan
                self.prev_tilt = curr_tilt
                self.prev_zoom = curr_zoom
            except Exception as e:
                self.log(f"Polling failed: {e}", "CRITICAL")
                self.log("Reconnecting to camera...", "INFO")
                if self.connect():
                    self.log("Reconnected to camera, resuming polling...", "INFO")
                else:
                    time.sleep(self.reconnect_time)

def start_camera_thread(config, log_level):
    app = ONVIFMonitorApp(config, min_level=log_level)
    if app.connect():
        app.run()

if __name__ == "__main__":
    LEVELS = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
    def log(message: str, level: str = 'INFO'):
        lvl_upper = level.upper()
        if LEVELS.get(lvl_upper, 1) < self.min_level_value:
            return
        severity_char = lvl_upper[0]
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"{now} - [{severity_char}] - [SYSTEM] - {message}")
    
    if os.path.exists('/data/options.json'):
        with open('/data/options.json') as f:
            config_data = json.load(f)
            camera_list = config_data.get('cameras', [])
            log_level = config_data.get('log_level', 'INFO')
    else:
        # Fallback to Environment Variables
        camera_list = [{
            'camera_name': os.getenv('CAMERA_NAME'),
            'host': os.getenv('host'),
            'port': int(os.getenv('PORT')),
            'username': os.getenv('USERNAME'),
            'password': os.getenv('PASSWORD'),
            'ignore_ssl': os.getenv('IGNORE_SSL', 'False').lower() == 'true',
            'reconnect_time': int(os.getenv('RECONNECT_TIME', '5')),
            'polling_interval': float(os.getenv('POLLING_INTERVAL', '0.3')),
            'fast_poll_on_move': os.getenv('FAST_POLL_ON_MOVE', 'True').lower() == 'true'
        }]
        log_level = os.getenv('LOG_LEVEL', 'INFO')

    if not camera_list:
        log("No cameras configured, check configuration", "CRITICAL")
        sys.exit(1)

    log(f"Started ONVIF PTZ Helper", "INFO")
    log(f"Cameras configured: {len(camera_list)}", "INFO")
    threads = []
    for config in camera_list:
        t = threading.Thread(target=start_camera_thread, args=(config, log_level))
        t.daemon = True
        threads.append(t)
        t.start()
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Exiting...", "INFO")






