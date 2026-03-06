import time
import sys
import threading
import json
import os
from datetime import datetime
from collections import deque
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
        self.idle_polling_interval = camera_config.get('idle_polling_interval', 0.3)
        self.active_polling_interval = camera_config.get('active_polling_interval', 0.3)
        self.active_polling_history = camera_config.get('active_polling_history', 2)
        self.min_level_value = self.LEVELS.get(min_level.upper(), 1)
        self.cam: Optional[onvif.ONVIFCamera] = None
        self.ptz_service = None
        self.media_service = None
        self.token = None
        self.history = deque(maxlen=self.active_polling_history)
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
                init_coords = (
                    status.Position.PanTilt.x,
                    status.Position.PanTilt.y,
                    status.Position.Zoom.x
                )
                self.log(f"Connected to '{self.camera_name}': {self.host}:{self.port}", "INFO")
                return True
            except Exception as e:
                self.log(f"Connection failed: {e}", "CRITICAL")
                self.log(f"Attempting to reconnect in {self.reconnect_time}s...", "INFO")
                time.sleep(self.reconnect_time)

    def send_stop_command(self):
        try:
            self.log("Sending stop command...", "INFO")
            self.ptz_service.Stop({'ProfileToken': self.token, 'PanTilt': True, 'Zoom': True})
            self.log("Stop command sent", "INFO")
        except Exception as e:
            self.log(f"Stop command failed: {e}", "ERROR")

    def run(self):
        self.log("Monitoring PTZ position...", "INFO")
        while True:
            try:
                status = self.ptz_service.GetStatus({'ProfileToken': self.token})
                curr_coords = (
                    status.Position.PanTilt.x,
                    status.Position.PanTilt.y,
                    status.Position.Zoom.x
                )
                curr_pantiltstatus = status.MoveStatus.PanTilt
                curr_zoomstatus = status.MoveStatus.PanTilt
                currently_moving = any(curr_coords != prev for prev in self.history)
                
                self.log(f"PTZ position: P:{curr_coords[0]} T:{curr_coords[1]} Z:{curr_coords[2]}", "DEBUG")
                self.log(f"PTZ position changing: {currently_moving}", "DEBUG")
                self.log(f"PTZ status: PanTilt: {curr_pantiltstatus}, Zoom: {curr_zoomstatus}", "DEBUG")

                if currently_moving:
                    if not self.is_currently_moving:
                        self.log("Movement detected, waiting for PTZ position to stabilise...", "INFO")
                        self.is_currently_moving = True
                    time.sleep(self.active_polling_interval)
                else:
                    if self.is_currently_moving:
                        self.log("PTZ position stabilised", "INFO")
                        self.send_stop_command()
                        self.is_currently_moving = False
                        self.log("Monitoring PTZ position...", "INFO")
                    time.sleep(self.idle_polling_interval)
                
                self.history.append(curr_coords)
            except Exception as e:
                self.log(f"Polling failed: {e}", "CRITICAL")
                self.log("Reconnecting to camera...", "INFO")
                if self.connect():
                    self.log("Reconnected to camera, resuming polling...", "INFO")
                else:
                    time.sleep(self.reconnect_time)

def systemlog(message: str, source: str = 'Unknown', level: str = 'INFO'):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    severity_char = level[0]
    print(f"{now} - [{severity_char}] - [{source}] - {message}")

def validate_and_start_cameras(camera_list, log_level):
    minimum_camera_values = {
        'reconnect_time': (0, 5.0),
        'idle_polling_interval': (0, 0.3),
        'active_polling_interval': (0, 0.3),
        'active_polling_history': (2, 2)
    }
    
    for config in camera_list:
        camera_name = config.get('camera_name', 'Unknown')
        
        for key, (min_allowed, default) in minimum_camera_values.items():
            val = config.get(key)
            
            # Case 1: Value is not set (None)
            if val is None:
                systemlog(f"'{key}' defaulted to {default}", camera_name, "DEBUG")
                config[key] = default
            
            # Case 2: Value is set but below minimum
            elif val < min_allowed:
                systemlog(
                    f"'{key}: {val}' is invalid. Defaulting to {default}. Check your configuration", camera_name, "WARNING"
                )
                config[key] = default
        
        t = threading.Thread(target=start_camera_thread, args=(config, log_level))
        t.daemon = True
        t.start()

def start_camera_thread(config, log_level):
    app = ONVIFMonitorApp(config, min_level=log_level)
    if app.connect():
        app.run()

if __name__ == "__main__":
    
    if os.path.exists('/data/options.json'):
        with open('/data/options.json') as f:
            config_data = json.load(f)
            log_level = config_data.get('log_level', 'INFO')
            camera_list = config_data.get('cameras', [])
    else:
        # Fallback to Environment Variables
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        camera_list = [{
            'camera_name': os.getenv('CAMERA_NAME'),
            'host': os.getenv('host'),
            'port': int(os.getenv('PORT')),
            'username': os.getenv('USERNAME'),
            'password': os.getenv('PASSWORD'),
            'ignore_ssl': os.getenv('IGNORE_SSL', 'False').lower() == 'true',
            'reconnect_time': float(os.getenv('RECONNECT_TIME', '5')),
            'idle_polling_interval': float(os.getenv('IDLE_POLLING_INTERVAL', '0.3')),
            'active_polling_interval': float(os.getenv('ACTIVE_POLLING_INTERVAL', '0.3')),
            'active_polling_history': int(os.getenv('ACTIVE_POLLING_HISTORY', '2')),
        }]

    if not camera_list:
        systemlog("Configuration error: no cameras configured, check configuration", "System", "CRITICAL")
        sys.exit(1)
    
    systemlog(f"Started ONVIF PTZ Helper. Cameras: {len(camera_list)}", "System", "INFO")
    validate_and_start_cameras(camera_list, log_level)
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        systemlog("Exiting...", "System", "WARNING")



