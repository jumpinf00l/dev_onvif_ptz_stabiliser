# Import standard Python libraries for timing, system signals, threading, and data handling
import time
import sys
import threading
import json
import os
from datetime import datetime
from collections import deque

# Import ONVIF and SOAP (zeep) libraries for camera communication protocols
import onvif
import zeep
from zeep.transports import Transport
import requests
from typing import Optional, Dict

# Global synchronization for thread-safe console output
print_lock = threading.Lock()
# Mapping of log levels to integers for priority-based filtering
log_levels = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
# Initial global threshold for logging (updated dynamically at runtime)
min_level_value = 1  

class ONVIFMonitorApp:
    """Class to manage monitoring and PTZ stop-command logic for a specific camera."""
    def __init__(self, camera_config: Dict, min_level: str = 'INFO'):
        # Load configuration from the provided dictionary
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
        
        # Internal state variables
        self.cam: Optional[onvif.ONVIFCamera] = None
        self.ptz_service = None
        self.media_service = None
        self.token = None
        self.history = deque(maxlen=self.active_polling_history)
        self.is_currently_moving = False
        
        # EFFICIENCY: Create and store the Transport layer once to reuse for all requests/reconnects
        self.transport = None
        if self.ignore_ssl:
            self.session = requests.Session()
            self.session.verify = False
            # Suppress warnings for unverified HTTPS requests
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
            self.transport = Transport(session=self.session)

    def connect(self):
        """Initialises the connection to the camera and discovers the required ONVIF services."""
        while True:
            try:
                log(f"Connecting to '{self.camera_name}': {self.host}:{self.port}...", self.camera_name, "INFO")
                
                # Instantiate the ONVIF camera client with the pre-allocated transport
                self.cam = onvif.ONVIFCamera(self.host, self.port, self.user, self.password, transport=self.transport)
                self.media_service = self.cam.create_media_service()
                self.ptz_service = self.cam.create_ptz_service()
                
                # Fetch media profiles to obtain the PTZ token needed for commands
                profiles = self.media_service.GetProfiles()
                if not profiles:
                    raise Exception("No ONVIF media service profiles found, cannot get PTZ token")
                
                self.token = profiles[0].token
                # Validate the connection by performing a test status request
                self.ptz_service.GetStatus({'ProfileToken': self.token})
                
                log(f"Connected to '{self.camera_name}': {self.host}:{self.port}", self.camera_name, "INFO")
                return True
            except Exception as e:
                log(f"Connection failed: {e}", self.camera_name, "CRITICAL")
                log(f"Attempting to reconnect in {self.reconnect_time}s...", self.camera_name, "INFO")
                time.sleep(self.reconnect_time)

    def send_stop_command(self):
        """Sends a PTZ Stop request to the camera to halt any ongoing pan, tilt, or zoom."""
        try:
            log(f"Sending stop command...", self.camera_name, "INFO")
            self.ptz_service.Stop({'ProfileToken': self.token, 'PanTilt': True, 'Zoom': True})
            log(f"Stop command sent", self.camera_name, "INFO")
        except Exception as e:
            log(f"Stop command failed: {e}", self.camera_name, "ERROR")

    def run(self):
        """Main monitoring loop that checks for PTZ movement and triggers stabilization logic."""
        log(f"Monitoring PTZ position...", self.camera_name, "INFO")
        
        # EFFICIENCY: Cache frequently called methods and objects to local variables
        profile_token = {'ProfileToken': self.token}
        get_status = self.ptz_service.GetStatus
        
        while True:
            try:
                # Query the camera for current position coordinates
                status = get_status(profile_token)
                curr_coords = (
                    status.Position.PanTilt.x,
                    status.Position.PanTilt.y,
                    status.Position.Zoom.x
                )
                
                # EFFICIENCY: Movement is detected if the current position differs from any in history
                currently_moving = any(curr_coords != prev for prev in self.history)
                
                log(f"PTZ position: P:{curr_coords[0]} T:{curr_coords[1]} Z:{curr_coords[2]}", self.camera_name, "DEBUG")
                log(f"PTZ position changing: {currently_moving}", self.camera_name, "DEBUG")

                if currently_moving:
                    # If movement is newly detected, change state and poll faster
                    if not self.is_currently_moving:
                        log(f"Movement detected, waiting for PTZ position to stabilise...", self.camera_name, "INFO")
                        self.is_currently_moving = True
                    time.sleep(self.active_polling_interval)
                else:
                    # If movement was active but has now stopped, finalise with a stop command
                    if self.is_currently_moving:
                        log(f"PTZ position stabilised", self.camera_name, "INFO")
                        self.send_stop_command()
                        self.is_currently_moving = False
                        log(f"Monitoring PTZ position...", self.camera_name, "INFO")
                    # Use a slower polling interval when the camera is idle
                    time.sleep(self.idle_polling_interval)
                
                # Update the history deque with the newest coordinates
                self.history.append(curr_coords)
            except Exception as e:
                # Handle unexpected disconnects or errors by attempting a full reconnection
                log(f"Polling failed: {e}", self.camera_name, "CRITICAL")
                log(f"Reconnecting to camera...", self.camera_name, "INFO")
                if self.connect():
                    # Update local cache variables with new service references after reconnecting
                    get_status = self.ptz_service.GetStatus
                    profile_token = {'ProfileToken': self.token}
                    log(f"Reconnected to camera, resuming polling...", self.camera_name, "INFO")
                else:
                    time.sleep(self.reconnect_time)

def log(message: str, source: str = 'Unknown', level: str = 'INFO'):
    """Utility for printing formatted logs with priority filtering and timestamping."""
    log_level_upper = level.upper()
    # EFFICIENCY: Check level first before performing string formatting or I/O
    if log_levels.get(log_level_upper, 1) < min_level_value:
        return
        
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    severity_char = level[0]
    with print_lock:
        print(f"{now} - [{severity_char}] - [{source}] - {message}")
        # Force the output to flush to the console immediately (crucial for Docker/Services)
        sys.stdout.flush()

def validate_and_start_cameras(camera_list, log_level):
    """Sanitises camera configurations and starts a dedicated thread for each camera."""
    minimum_camera_values = {
        'reconnect_time': (0, 5.0),
        'idle_polling_interval': (0, 0.3),
        'active_polling_interval': (0, 0.3),
        'active_polling_history': (2, 2)
    }
    
    for config in camera_list:
        camera_name = config.get('camera_name', 'Unknown')
        
        # Verify and default any missing or invalid configuration keys
        for key, (min_allowed, default) in minimum_camera_values.items():
            val = config.get(key)
            if val is None:
                log(f"Defaulted '{key}' to {default}", camera_name, "DEBUG")
                config[key] = default
            elif val < min_allowed:
                log(f"'{key}: {val}' is invalid. Defaulting to {default}.", camera_name, "WARNING")
                config[key] = default
        
        # Launch each camera monitor as a background daemon thread
        t = threading.Thread(target=start_camera_thread, args=(config, log_level))
        t.daemon = True
        t.start()

def start_camera_thread(config, log_level):
    """Helper function to initialise and run the application instance within a thread."""
    app = ONVIFMonitorApp(config, min_level=log_level)
    if app.connect():
        app.run()

if __name__ == "__main__":
    # Attempt to load configuration from the standard Home Assistant options path
    if os.path.exists('/data/options.json'):
        with open('/data/options.json') as f:
            config_data = json.load(f)
            log_level = config_data.get('log_level', 'INFO')
            camera_list = config_data.get('cameras', [])
    else:
        # Fallback to Environment Variables for standalone or testing environments
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        camera_list = [{
            'camera_name': os.getenv('CAMERA_NAME'),
            'host': os.getenv('host'),
            'port': int(os.getenv('PORT') or 80),
            'username': os.getenv('USERNAME'),
            'password': os.getenv('PASSWORD'),
            'ignore_ssl': os.getenv('IGNORE_SSL', 'False').lower() == 'true',
            'reconnect_time': float(os.getenv('RECONNECT_TIME', '5')),
            'idle_polling_interval': float(os.getenv('IDLE_POLLING_INTERVAL', '0.3')),
            'active_polling_interval': float(os.getenv('ACTIVE_POLLING_INTERVAL', '0.3')),
            'active_polling_history': int(os.getenv('ACTIVE_POLLING_HISTORY', '2')),
        }]

    # Set the global logging threshold based on the provided config
    min_level_value = log_levels.get(log_level.upper(), 1)
    
    # Ensure there is at least one camera configured before proceeding
    if not camera_list or not camera_list[0].get('host'):
        log(f"Configuration error: no cameras configured.", "System", "CRITICAL")
        sys.exit(1)
    
    log(f"Started ONVIF PTZ Helper. Cameras: {len(camera_list)}", "System", "INFO")
    
    # Validate settings and launch the camera threads
    validate_and_start_cameras(camera_list, log_level)
        
    # Keep the main process alive so daemon threads can continue to run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log(f"Keyboard interrupt, exiting...", "System", "WARNING")
