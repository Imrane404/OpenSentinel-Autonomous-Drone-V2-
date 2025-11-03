# -*- coding: utf-8 -*-
"""
🚁 ULTIMATE AUTONOMOUS DRONE - Corrected Version
==============================================

APPLIED CORRECTIONS:
✅ Video route corrected (/video_feed au lieu de /video)
✅ MJPEG stream optimized to avoid blocks
✅ Improved threading management
✅ Timeouts added to avoid freezes

Changements principaux:
- Ligne 951: Route changed from "/video" à "/video_feed"
- Ligne 1012: Image source changed from "/video" à "/video_feed"
- Ligne 940-949: Optimisation de gen_mjpeg() avec timeout
- Added drone state checks

Installation:
  pip install ultralytics opencv-contrib-python numpy flask pyyaml

Author: Imrane404
Date: 2025 (Corrected Version)
"""

import os
import sys
import time
import math
import threading
import logging
import json
import yaml
from collections import deque
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import numpy as np
import cv2
from flask import Flask, Response, request, redirect, jsonify, render_template_string, send_file

try:
    from ultralytics import YOLO
except:
    raise SystemExit("[FATAL] pip install ultralytics")

from controller import Robot


# ============================================================================

# ============================================================================
# DRONE ACTION LOGGER
# ============================================================================

class DroneActionLogger:
    def __init__(self, log_file="drone_flight_log.json"):
        self.log_file = log_file
        self.sesifon_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs = []
        self.lock = __import__('threading').Lock()
        self.start_time = __import__('time').time()
        
        # 🆕 REAL-TIME ACTIVATABLE EVENT FILTERS
        self.event_filters = {
            "takeoff": True,
            "land": True,
            "emergency": True,
            "detection": False,
            "velocity": False,  # Disabled by default for performance
            "position": False,
            "mode_change": False,
            "tracking": False,
            "command": False,
            "photo": False,
            "video": False,
            "waypoint": False,
            "geofence": False,
            "battery": False,
            "imu_data": False,           # 🆕 IMU data (very high frequency)
            "altitude_control": False,   # 🆕 Altitude control (very high frequency)
            "control_commands": False,
            "motor_velocities": False,   # 🆕 Motor speeds (very high frequency)
            "follow_active": False,
            "other": False
        }
        
        self._init_log_file()
    
    def _init_log_file(self):
        import json
        with open(self.log_file, 'w') as f:
            json.dump({
                "sesifon_id": self.sesifon_id, 
                "start_time": datetime.now().isoformat(), 
                "events": [],
                "event_filters": self.event_filters.copy()
            }, f, indent=2)
    
    def set_event_filter(self, event_type, enabled):
        """Enable/disable an event type in real-time"""
        with self.lock:
            if event_type in self.event_filters:
                self.event_filters[event_type] = enabled
                return True
            return False
    
    def get_event_filters(self):
        """Return current filter state"""
        with self.lock:
            return self.event_filters.copy()
    
    def log_event(self, event_type, data):
        """Log an event only if its filter is enabled"""
        import time
        
        # 🆕 FILTER CHECK
        with self.lock:
            # Categorize event
            category = event_type
            if event_type not in self.event_filters:
                category = "other"
            
            # Ne logger que if le filtre est enabled
            if not self.event_filters.get(category, True):
                return
            
            event = {
                "timestamp": datetime.now().isoformat(), 
                "elapsed_time": round(time.time() - self.start_time, 3), 
                "event_type": event_type, 
                "data": data
            }
            self.logs.append(event)
            if len(self.logs) % 10 == 0 or event_type in ['takeoff', 'land', 'emergency', 'detection']:
                self._flush_to_file()
    
    def _flush_to_file(self):
        import json
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            data['events'].extend(self.logs)
            data['last_update'] = datetime.now().isoformat()
            data['total_events'] = len(data['events'])
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logs = []
        except: pass
    
    def finalize(self):
        import json, time
        self._flush_to_file()
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            data['end_time'] = datetime.now().isoformat()
            data['total_duration'] = round(time.time() - self.start_time, 2)
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except: pass

# CONFIGURATION & CONSTANTS
# ============================================================================

def clamp(v, vmin, vmax):
    return vmin if v < vmin else vmax if v > vmax else v


def distance_2d(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


class DroneMode(Enum):
    MANUAL = "manual"
    SEARCH = "search"
    FOLLOW = "follow"
    ORBIT = "orbit"
    WAYPOINT = "waypoint"
    RTH = "return_to_home"


@dataclass
class Waypoint:
    x: float
    y: float
    z: float
    action: str = "goto"  # goto, search, photo, hover
    params: dict = None


LABEL_MAPPING = {
    "personne": "person", "voiture": "car", "auto": "car", "camion": "truck",
    "bus": "bus", "velo": "bicycle", "moto": "motorcycle", "chien": "dog",
    "chat": "cat", "oiseau": "bird", "cheval": "horse",
}


def normalize_label(text):
    text = text.lower().strip()
    for color in ["rouge", "red", "blanc", "white", "noir", "black", "bleu", "blue", "vert", "green"]:
        text = text.replace(color, "").strip()
    return LABEL_MAPPING.get(text, text)

# ============================================================================
# CACHED STATUS DATA (FIX POUR /status LENT)
# ============================================================================

class CachedStatus:
    """Cache to avoid recalculating status data at each request"""
    
    def __init__(self, cache_duration=0.1):  # 100ms cache
        self.cache_duration = cache_duration
        self.last_update = 0
        self.cached_data = None
        self.lock = threading.Lock()
    
    def get(self, update_func):
        """Return cached data or update it"""
        now = time.time()
        
        with self.lock:
            if self.cached_data is None or (now - self.last_update) > self.cache_duration:
                self.cached_data = update_func()
                self.last_update = now
            
            return self.cached_data.copy()


# ============================================================================
# HYBRID TRACKER (YOLO + KCF)
# ============================================================================

class HybridTracker:
    """STABLE hybrid detector with YOLO + KCF fusion"""
    
    def __init__(self, yolo_model, target_class, min_bbox_size=15):
        import queue as q
        
        self.yolo = yolo_model
        self.target_class = target_class
        self.min_bbox_size = min_bbox_size
        
        # Tracking
        self.tracker = None
        self.tracking_active = False
        self.last_detection_time = 0
        self.redetect_interval = 0.3  # 🔧 REDUCED for reactive tracking
        
        # State
        self.bbox = None
        self.confidence = 0.0
        self.tracking_failures = 0
        self.max_failures = 15  # INCREASED: 5 → 15 (more tolerant)
        self.track_id = 0
        
        # NOUVEAU: Filtrage temporel
        self.last_valid_bbox = None
        self.last_valid_time = 0
        self.validity_duration = 1.0  # Keep detection for 1 second
        
        # NEW: History for stability
        self.detection_history = []
        self.history_size = 5
        
        # Queue for asynchronous YOLO detections
        self.detection_queue = q.Queue(maxsize=1)
        self.frame_queue = q.Queue(maxsize=1)
        self.detection_thread = None
        self.detection_running = False
    
    def start_detection_thread(self):
        """Démarre le thread de détection YOLO"""
        if not self.detection_running:
            self.detection_running = True
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
    
    def stop_detection_thread(self):
        """Arrête le thread de détection"""
        self.detection_running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=1.0)
    
    def _detection_loop(self):
        """Boucle de détection YOLO en arrière-plan"""
        import queue as q
        while self.detection_running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                bbox = self._detect_with_yolo_sync(frame)
                try:
                    self.detection_queue.put_nowait(bbox)
                except q.Full:
                    pass
            except q.Empty:
                time.sleep(0.01)
            except Exception as e:
                print(f"[HybridTracker] Detection error: {e}")
                time.sleep(0.1)
    
    def _detect_with_yolo_sync(self, frame):
        """Detection YOLO synchrone"""
        try:
            results = self.yolo(frame, conf=0.25, verbose=False)[0]
            best_box = None
            best_area = -1.0
            
            for box in results.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.yolo.names[cls_id]
                conf = float(box.conf[0])
                
                if cls_name.lower() != self.target_class.lower():
                    continue
                
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                w = x2 - x1
                h = y2 - y1
                
                if w < self.min_bbox_size or h < self.min_bbox_size:
                    continue
                
                area = w * h
                if area > best_area:
                    best_area = area
                    best_box = (x1, y1, x2, y2, cls_name, conf)
            
            return best_box
        except Exception as e:
            print(f"[HybridTracker] YOLO error: {e}")
            return None
    
    def request_detection(self, frame):
        """Demande une détection YOLO (non-bloquant)"""
        import queue as q
        try:
            self.frame_queue.put_nowait(frame.copy())
        except q.Full:
            pass
    
    def get_detection_result(self):
        """Récupère le résultat de détection YOLO"""
        import queue as q
        try:
            return self.detection_queue.get_nowait()
        except q.Empty:
            return None
    
    def init_tracker(self, frame, bbox):
        """Initialise le tracker KCF"""
        x1, y1, x2, y2, name, score = bbox
        self.tracker = cv2.legacy.TrackerKCF_create()
        tracker_bbox = (x1, y1, x2 - x1, y2 - y1)
        self.tracker.init(frame, tracker_bbox)
        self.tracking_active = True
        self.tracking_failures = 0
        self.bbox = bbox
        self.confidence = score
        self.last_detection_time = time.time()
        self.track_id += 1
    
    def _add_to_history(self, bbox):
        """Ajoute une détection à l'historique"""
        if bbox:
            self.detection_history.append(bbox)
            if len(self.detection_history) > self.history_size:
                self.detection_history.pop(0)
    
    def _get_stable_detection(self):
        """Retourne une détection stable basée sur l'historique"""
        if not self.detection_history:
            return None
        
        # Average positions for stability
        x1_avg = sum(d[0] for d in self.detection_history) / len(self.detection_history)
        y1_avg = sum(d[1] for d in self.detection_history) / len(self.detection_history)
        x2_avg = sum(d[2] for d in self.detection_history) / len(self.detection_history)
        y2_avg = sum(d[3] for d in self.detection_history) / len(self.detection_history)
        
        last_det = self.detection_history[-1]
        
        return (int(x1_avg), int(y1_avg), int(x2_avg), int(y2_avg), last_det[4], last_det[5])
    
    def update(self, frame):
        """Mise à jour STABLE du tracker avec fusion YOLO + KCF"""
        current_time = time.time()
        
        # Check if une nouvelle détection YOLO est disponible
        yolo_result = self.get_detection_result()
        
        if yolo_result:
            # NOUVELLE DÉTECTION YOLO
            # Ajouter at l'historique
            self._add_to_history(yolo_result)
            
            # Sauvegarder comme dernière détection valide
            self.last_valid_bbox = yolo_result
            self.last_valid_time = current_time
            
            # Reset or mettre update le tracker
            if not self.tracking_active:
                self.init_tracker(frame, yolo_result)
            else:
                # FUSION: mise update without réinit
                self.bbox = yolo_result
                self.confidence = yolo_result[5]
                self.tracking_failures = 0
                self.last_detection_time = current_time
            
            return self._get_stable_detection()
        
        # No new détection YOLO
        if not self.tracking_active:
            # NOUVEAU: Utiliser dernière détection valide if récente
            if self.last_valid_bbox and (current_time - self.last_valid_time) < self.validity_duration:
                self.request_detection(frame)
                return self.last_valid_bbox
            
            self.request_detection(frame)
            return None
        
        # Demander re-détection périodique
        if current_time - self.last_detection_time > self.redetect_interval:
            self.request_detection(frame)
        
        # Mise update du tracker KCF
        success, tracker_bbox = self.tracker.update(frame)
        
        if success:
            x, y, w, h = [int(v) for v in tracker_bbox]
            x1, y1 = x, y
            x2, y2 = x + w, y + h
            
            # Clamp aux limites
            h_img, w_img = frame.shape[:2]
            x1 = max(0, min(x1, w_img - 1))
            x2 = max(0, min(x2, w_img - 1))
            y1 = max(0, min(y1, h_img - 1))
            y2 = max(0, min(y2, h_img - 1))
            
            self.tracking_failures = 0
            
            # Confiance STABLE
            name = self.bbox[4] if self.bbox else self.target_class
            conf = self.confidence  # Garde confiance YOLO
            
            self.bbox = (x1, y1, x2, y2, name, conf)
            
            # Ajouter at l'historique
            self._add_to_history(self.bbox)
            
            # Update dernière détection valide
            self.last_valid_bbox = self.bbox
            self.last_valid_time = current_time
            
            return self._get_stable_detection()
        else:
            # Tracking a failed
            self.tracking_failures += 1
            
            # NOUVEAU: Utiliser dernière détection valide if récente
            if self.last_valid_bbox and (current_time - self.last_valid_time) < self.validity_duration:
                return self.last_valid_bbox
            
            # Trop d'échecs: désactiver tracking
            if self.tracking_failures >= self.max_failures:
                self.tracking_active = False
                self.tracker = None
                self.request_detection(frame)
            
            return self.bbox


# ============================================================================
# VIDEO RECORDER
# ============================================================================

class VideoRecorder:
    """Enregistreur vidéo HD"""
    
    def __init__(self, filename, width, height, fps=30):
        self.filename = filename
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        self.frame_count = 0
        self.start_time = time.time()
    
    def write(self, frame):
        if self.writer.isOpened():
            self.writer.write(frame)
            self.frame_count += 1
    
    def get_duration(self):
        return time.time() - self.start_time
    
    def release(self):
        if self.writer:
            self.writer.release()
        return self.filename, self.frame_count, self.get_duration()


# ============================================================================
# MISSION EXECUTOR
# ============================================================================

class MisifonExecutor:
    """Exécuteur de missions automatisées"""
    
    def __init__(self, drone):
        self.drone = drone
        self.mission = []
        self.current_step = 0
        self.running = False
        self.waypoint_threshold = 0.3  # mètres
    
    def add_waypoint(self, wp):
        self.mission.append(wp)
    
    def clear_misifon(self):
        self.mission = []
        self.current_step = 0
        self.running = False
    
    def start(self):
        if not self.mission:
            return False
        self.running = True
        self.current_step = 0
        return True
    
    def stop(self):
        self.running = False
    
    def update(self):
        if not self.running or not self.mission:
            return False
        
        if self.current_step >= len(self.mission):
            self.running = False
            return False
        
        wp = self.mission[self.current_step]
        x, y, z = self.drone.gps.getValues()
        
        dist = distance_2d((x, y), (wp.x, wp.y))
        alt_diff = abs(z - wp.z)
        
        if dist < self.waypoint_threshold and alt_diff < 0.5:
            if wp.action == "photo":
                self.drone.take_photo()
            elif wp.action == "hover":
                time.sleep(wp.params.get("duration", 2.0) if wp.params else 2.0)
            
            self.current_step += 1
            return True
        
        # Navigation vers le waypoint
        self.drone._navigate_to(wp.x, wp.y, wp.z)
        return True


# ============================================================================
# BATTERY MANAGER
# ============================================================================

class BatteryManager:
    """Gestion intelligente de la batterie"""
    
    def __init__(self, initial_charge=100.0):
        self.charge = initial_charge
        self.start_time = time.time()
        self.last_update = self.start_time
        
        self.drain_rate_hover = 1.0  # %/min
        self.drain_rate_moving = 2.5  # %/min
        
        self.low_battery_threshold = 20.0
        self.critical_battery_threshold = 10.0
    
    def update(self, is_moving=False):
        now = time.time()
        dt = (now - self.last_update) / 60.0  # en minutes
        
        if dt > 0:
            rate = self.drain_rate_moving if is_moving else self.drain_rate_hover
            self.charge -= rate * dt
            self.charge = max(0.0, self.charge)
            self.last_update = now
    
    def get_percentage(self):
        return self.charge
    
    def is_low(self):
        return self.charge < self.low_battery_threshold
    
    def is_critical(self):
        return self.charge < self.critical_battery_threshold


# ============================================================================
# ULTIMATE DRONE CONTROLLER
# ============================================================================

class UltimateDroneController(Robot):
    """Drone controller ultime avec système de contrôle original"""
    
    # Gains moteurs (DEPUIS FICHIER ORIGINAL)
    K_VERTICAL_THRUST = 72.0  # 🔧 AUGMENTÉ: 68.5 → 72.0 for permettre décollage depuis sol
    K_VERTICAL_OFFSET = 0.6
    K_VERTICAL_P = 3.0
    K_ROLL_P = 50.0
    K_PITCH_P = 30.0
    
    # PID centrage (OPTIMISÉ to avoid oscillations)
    CX_KP, CX_KD = 0.004, 0.0012  # RÉDUIT: 0.0065 → 0.004 (less agresiff)
    SZ_KP, SZ_KD = 0.015, 0.0050  # 🔧 FIXED: Gains augmentés x6 for approche efficace
    
    # Rotation (OPTIMISÉ for stabilité)
    K_YAW_RATE = 2.0  # RÉDUIT: 3.0 → 2.0 (rotation more douce)
    SWEEP_RATE = math.radians(45.0)
    
    # Dead zone to avoid oscillations
    YAW_DEADZONE = 15.0  # pixels - ignore les errors < 15px
    
    # Detection
    MIN_BBOX_SIZE = 15
    
    # Modes autonomes
    FOLLOW_DISTANCE = 3.0
    ORBIT_RADIUS = 5.0
    ORBIT_SPEED = 0.2
    
    HTTP_PORT = int(os.getenv("PORT", "5010"))
    
    def __init__(self):
        super().__init__()

        # Logger système
        self.action_logger = DroneActionLogger("drone_flight_log.json")
        self._last_movement_log_time = time.time()
        
        self.time_step = int(self.getBasicTimeStep())
        
        # Camera
        self.camera = self.getDevice("camera")
        self.camera.enable(self.time_step)
        self.cam_w = self.camera.getWidth()
        self.cam_h = self.camera.getHeight()
        
        # GPS & IMU
        self.imu = self.getDevice("inertial unit")
        self.imu.enable(self.time_step)
        
        self.gps = self.getDevice("gps")
        self.gps.enable(self.time_step)
        
        self.gyro = self.getDevice("gyro")
        self.gyro.enable(self.time_step)
        
        # Moteurs
        self.motors = {
            "front_left": self.getDevice("front left propeller"),
            "front_right": self.getDevice("front right propeller"),
            "rear_left": self.getDevice("rear left propeller"),
            "rear_right": self.getDevice("rear right propeller"),
        }
        for m in self.motors.values():
            m.setPosition(float('inf'))
            m.setVelocity(1.0)  # Rotation lente au démarrage (mode "idle")
        
        # State
        self._state_lock = threading.Lock()
        self.drone_mode = DroneMode.MANUAL
        self.flying = False  # Renommé for correspondre au fichier original
        self.is_flying = False  # Keep for compatibility
        self.target_alt = 1.50  # 🔧 FIXED: Altitude augmentée
        self.target_altitude = 1.50  # 🔧 Pour compatibilité
        
        # PID for contrôle (DEPUIS FICHIER ORIGINAL)
        self._cx_prev = 0.0
        self._sz_prev = 0
        self._err_x_prev = 0.0  # 🎯 Pour suivi visuel yaw.0
        self._yaw_override = 0.0
        
        # Bbox for tracking (DEPUIS FICHIER ORIGINAL)
        self._bbox = None
        self._bbox_ema = None
        
        # YOLO + Tracker
        model_path = os.path.join(os.path.dirname(__file__), "yolo11n.pt")
        if not os.path.exists(model_path):
            self._ring(logging.INFO, "📥 Downloading YOLO11n...")
            self.yolo_model = YOLO("yolo11n.pt")
            self.yolo_model.export(format="onnx")
        else:
            self.yolo_model = YOLO(model_path)
        
        self.hybrid_tracker = None
        self.search_target = None
        
        # Batterie
        self.battery = BatteryManager()
        
        # Misifons
        self.misifon_executor = MisifonExecutor(self)
        
        # Home position
        self.home_position = None
        
        # Geofence
        self.geofence_radius = 50.0  # mètres
        
        # Recording
        self.video_recorder = None
        self.photo_counter = 0
        
        # UI
        self.HTTP_PORT = 5010
        self._ui_started = False
        self._status_cache = CachedStatus(cache_duration=0.1)
        self._ui_thread = None
        self._ui_logs = deque(maxlen=100)
        self._gps_trace = deque(maxlen=500)
        self._shutdown = False
        
        # FPS
        self._det_times = deque(maxlen=30)
        self._last_frame = None
        self._frame_lock = threading.Lock()
        
        # Controls manuels (ENHANCED)
        self.manual_controls = {
            'z': False, 's': False, 'q': False, 
            'd': False, 'a': False, 'e': False,
        }
        self.manual_pitch = 0.0
        self.manual_yaw = 0.0
        self.manual_altitude_delta = 0.0
        self.sweep_rate_adjustable = math.radians(45.0)  # Speed rotation réglable
        
        # Logging
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        self._logger = logging.getLogger("Drone")
    
    def _ring(self, level, msg):
        self._logger.log(level, msg)
        self._ui_logs.append("[{}] {}".format(time.strftime("%H:%M:%S"), msg))
    
    def det_fps(self):
        """Calculatee FPS (VERSION ORIGINALE QUI FONCTIONNAIT)"""
        if not self._det_times:
            return 0.0
        avg = sum(self._det_times) / len(self._det_times)
        return 1.0 / avg if avg > 1e-6 else 0.0
    
    def get_camera_bgr(self):
        """Récupère l'image de la caméra (VERSION ORIGINALE QUI FONCTIONNAIT)"""
        try:
            raw = self.camera.getImage()
        except (ValueError, AttributeError):
            return None
        if raw is None:
            return None
        buf = np.frombuffer(raw, dtype=np.uint8)
        if buf.size != self.cam_w * self.cam_h * 4:
            img = np.zeros((self.cam_h, self.cam_w, 3), np.uint8)
            for y in range(self.cam_h):
                for x in range(self.cam_w):
                    r = self.camera.imageGetRed(raw, self.cam_w, x, y)
                    g = self.camera.imageGetGreen(raw, self.cam_w, x, y)
                    b = self.camera.imageGetBlue(raw, self.cam_w, x, y)
                    img[y, x] = [b, g, r]
            bgr = img
        else:
            bgra = buf.reshape((self.cam_h, self.cam_w, 4))
            bgr = bgra[:, :, :3].copy(order="C")
        
        with self._frame_lock:
            self._last_frame = bgr
        return bgr
    
    def take_photo(self):
        """Prend une photo"""
        frame = self.get_camera_bgr()
        if frame is not None:
            filename = "photo_{:04d}.jpg".format(self.photo_counter)
            cv2.imwrite(filename, frame)
            self.photo_counter += 1
            self._ring(logging.INFO, "📸 Photo saved: {}".format(filename))
    
    def _cmd_takeoff(self):
        """Takeoff"""
        self.action_logger.log_event("takeoff", {"message": "Drone taking off"})
        with self._state_lock:
            self.flying = True
            self.is_flying = True  # Pour compatibilité
            self.drone_mode = DroneMode.MANUAL
            if self.home_position is None:
                x, y, z = self.gps.getValues()
                self.home_position = (x, y, 0)
        
        self._ring(logging.INFO, "🛫 Taking off...")
    
    def _cmd_land(self):
        """Landing en douceur (ENHANCED)"""
        self.action_logger.log_event("land", {"message": "Drone landing"})
        self._ring(logging.INFO, "🛬 Landing...")
        
        with self._state_lock:
            if self.hybrid_tracker:
                self.hybrid_tracker.stop_detection_thread()
                self.hybrid_tracker = None
            self.drone_mode = DroneMode.MANUAL
            self._bbox = None
            self._bbox_ema = None
        
        # ENHANCED: Descente progresifve
        try:
            x, y, z = self.gps.getValues()
            target_height = 0.3
            descent_rate = 1.5  # m/s (more rapide)
            
            while z > target_height and not self._shutdown:
                x, y, z = self.gps.getValues()
                self.target_alt = max(target_height, z - descent_rate * 0.05)
                time.sleep(0.05)  # Mise update more fréquente
            
            self.flying = False
            self.is_flying = False
            
            # Réduction rapide des moteurs
            for velocity in range(10, 0, -2):  # Par pas of 2 au lieu of 1
                for m in self.motors.values():
                    m.setVelocity(velocity / 10.0)
                time.sleep(0.02)  # Plus rapide
            
            for m in self.motors.values():
                m.setVelocity(1.0)
            
            self._ring(logging.INFO, "✅ Landed safely")
        except Exception as e:
            self._ring(logging.ERROR, f"Land error: {e}")
            self.flying = False
            self.is_flying = False
    
    def _cmd_emergency_stop(self):
        """Arrêt d'urgence avec descente contrôlée (ENHANCED)"""
        self.action_logger.log_event("emergency", {"message": "Emergency stop"})
        self._ring(logging.WARNING, "🚨 EMERGENCY LANDING!")
        
        with self._state_lock:
            if self.hybrid_tracker:
                self.hybrid_tracker.stop_detection_thread()
                self.hybrid_tracker = None
            self.drone_mode = DroneMode.MANUAL
        
        # ENHANCED: Descente d'urgence mais contrôlée
        try:
            x, y, z = self.gps.getValues()
            target_height = 0.2
            descent_rate = 2.5  # Descente rapide (5x more rapide)
            
            while z > target_height and not self._shutdown:
                x, y, z = self.gps.getValues()
                self.target_alt = max(target_height, z - descent_rate * 0.05)
                time.sleep(0.05)
            
            self.flying = False
            self.is_flying = False
            
            for m in self.motors.values():
                m.setVelocity(1.0)
            
            self._ring(logging.WARNING, "⚠️ Emergency landing completed")
        except Exception as e:
            self._ring(logging.ERROR, f"Emergency error: {e}")
            for m in self.motors.values():
                m.setVelocity(0.0)
            self.flying = False
            self.is_flying = False
    
    def _cmd_start_search(self, query):
        """Lance une recherche d'objet"""
        normalized = normalize_label(query)
        self.search_target = normalized
        
        self.hybrid_tracker = HybridTracker(self.yolo_model, normalized)
        self.hybrid_tracker.start_detection_thread()  # CRITICAL: Start le thread
        self.drone_mode = DroneMode.SEARCH
        
        self._ring(logging.INFO, "🔍 Searching for: {}".format(normalized))
    
    def _cmd_stop_search(self):
        """Arrête la recherche (ENHANCED: arrêt rotation)"""
        with self._state_lock:
            if self.hybrid_tracker:
                self.hybrid_tracker.stop_detection_thread()  # CRITICAL: Stop le thread
            self.drone_mode = DroneMode.MANUAL
            self.hybrid_tracker = None
            self.search_target = None
            self._bbox = None
            self._bbox_ema = None
            
            # ENHANCED: Stop rotation
            self._yaw_override = 0.0
            self.manual_yaw = 0.0
        
        self._ring(logging.INFO, "⏹ Search stopped")
    
    def _cmd_follow_mode(self):
        """Active le mode Follow"""
        if self.hybrid_tracker and self.hybrid_tracker.tracking_active:
            self.drone_mode = DroneMode.FOLLOW
            self._ring(logging.INFO, "🎯 Follow mode activated")
    
    def _cmd_orbit_mode(self):
        """Active le mode Orbit"""
        if self.hybrid_tracker and self.hybrid_tracker.tracking_active:
            self.drone_mode = DroneMode.ORBIT
            self._ring(logging.INFO, "🔄 Orbit mode activated")
    
    def _cmd_return_home(self):
        """Retour à la maison"""
        self.action_logger.log_event("return_to_home", {"message": "RTH"})
        if self.home_position:
            self.drone_mode = DroneMode.RTH
            self._ring(logging.INFO, "🏠 Returning home...")
    
    def _cmd_start_recording(self):
        """Démarre l'enregistrement vidéo"""
        if not self.video_recorder:
            filename = "recording_{}.mp4".format(time.strftime("%Y%m%d_%H%M%S"))
            self.video_recorder = VideoRecorder(filename, self.cam_w, self.cam_h)
            self._ring(logging.INFO, "🔴 Recording started: {}".format(filename))
    
    def _cmd_stop_recording(self):
        """Arrête l'enregistrement vidéo"""
        if self.video_recorder:
            fname, frames, duration = self.video_recorder.release()
            self.action_logger.log_event("video_stop", {})
            self.video_recorder = None
            self._ring(logging.INFO, "⏹ Recording stopped: {} ({:.1f}s, {} frames)".format(
                fname, duration, frames))
    
    def _navigate_to(self, target_x, target_y, target_z):
        """Navigation vers un point"""
        x, y, z = self.gps.getValues()
        
        dx = target_x - x
        dy = target_y - y
        dz = target_z - z
        
        dist_2d = math.sqrt(dx**2 + dy**2)
        
        if dist_2d > 0.1:
            vx = dx / dist_2d * 0.5
            vy = dy / dist_2d * 0.5
        else:
            vx, vy = 0.0, 0.0
        
        vz = dz * 2.0
        
        self._apply_velocity(vx, vy, vz, 0.0)
    
    def _apply_velocity(self, vx, vy, vz, yaw_rate):
        """Applique une vélocité au drone"""
        vx = clamp(vx, -1.0, 1.0)
        vy = clamp(vy, -1.0, 1.0)
        vz = clamp(vz, -2.0, 2.0)
        yaw_rate = clamp(yaw_rate, -1.0, 1.0)
        
        # CORRECTION: base_speed augmentée for assurer le vol
        base_speed = 68.0  # Speed nécessaire for maintenir le vol
        
        # Calculate ifmplifié des vitesses moteurs
        m1 = base_speed + vz * 10 + vy * 5 - vx * 5 + yaw_rate * 5
        m2 = base_speed + vz * 10 - vy * 5 - vx * 5 - yaw_rate * 5
        m3 = base_speed + vz * 10 - vy * 5 + vx * 5 + yaw_rate * 5
        m4 = base_speed + vz * 10 + vy * 5 + vx * 5 - yaw_rate * 5
        
        self.motors["front_left"].setVelocity(m1)
        self.motors["front_right"].setVelocity(m2)
        self.motors["rear_left"].setVelocity(m3)
        self.motors["rear_right"].setVelocity(m4)
    
    def _check_geofence(self):
        """Vérifie le geofencing"""
        if not self.home_position:
            return True
        
        x, y, _ = self.gps.getValues()
        home_x, home_y, _ = self.home_position
        
        dist = distance_2d((x, y), (home_x, home_y))
        
        if dist > self.geofence_radius:
            self._ring(logging.WARNING, "⚠️ Geofence breach! Returning home...")
            self._cmd_return_home()
            return False
        
        return True
    
    def _control_step(self):
        """Control loop principale (DEPUIS FICHIER ORIGINAL)"""
        # Mesure FPS (VERSION ORIGINALE)
        t0 = time.time()
        
        # Mode idle if pas en vol
        if not self.flying:
            for m in self.motors.values():
                m.setVelocity(1.0)
            return
        
        # Lecture capteurs
        roll, pitch, yaw = self.imu.getRollPitchYaw()
        
        # LOG 32: IMU data
        self.action_logger.log_event("imu_data", {
            "roll": round(roll, 4),
            "pitch": round(pitch, 4),
            "yaw": round(yaw, 4)
        })
        
        x, y, z = self.gps.getValues()
        roll_rate, pitch_rate, yaw_rate = self.gyro.getValues()
        
        # Trace GPS
        self._gps_trace.append((x, y, time.time()))
        
        # LOG 2: Position périodique (toutes les 2 secondes)
        now = time.time()
        if not hasattr(self, '_last_position_log'):
            self._last_position_log = 0
        if now - self._last_position_log > 2.0:
            self.action_logger.log_event("position", {
                "x": round(x, 2),
                "y": round(y, 2),
                "z": round(z, 2),
                "mode": self.drone_mode.value,
                "battery": 100
            })
            self._last_position_log = now
        
        # Control stabilisation (PID ORIGINAL)
        roll_disturbance = 0.0
        pitch_disturbance = 0.0
        yaw_disturbance = 0.0
        
        roll_input = self.K_ROLL_P * clamp(roll, -1, 1) + roll_rate + roll_disturbance
        pitch_input = self.K_PITCH_P * clamp(pitch, -1, 1) + pitch_rate + pitch_disturbance
        alt_err = clamp(self.target_alt - z + self.K_VERTICAL_OFFSET, -1, 1)
        vertical_input = self.K_VERTICAL_P * (alt_err ** 3)
        
        # LOG 15: Altitude control
        self.action_logger.log_event("altitude_control", {
            "target": round(self.target_alt, 2),
            "current": round(z, 2),
            "error": round(self.target_alt - z, 3),
            "vertical_input": round(vertical_input, 3)
        })
        
        yaw_corr = 0.0
        pitch_corr = 0.0
        
        # CRITICAL FIX: Update le hybrid_tracker for obtenir les détections
        if self.hybrid_tracker:
            frame_bgr = self.get_camera_bgr()
            if frame_bgr is not None:
                detection = self.hybrid_tracker.update(frame_bgr)
                if detection:
                    with self._state_lock:
                        self._bbox = detection
                        # Smooth EMA
                        if self._bbox_ema is None:
                            self._bbox_ema = detection
                        else:
                            # EMA sur les coordonnées uniquement
                            x1_new, y1_new, x2_new, y2_new, name, score = detection
                            x1_old, y1_old, x2_old, y2_old, _, _ = self._bbox_ema
                            alpha = 0.95  # 🔧 AUGMENTÉ: 0.7 → 0.95 for suivi ultra-réactif
                            x1_ema = int(alpha * x1_new + (1 - alpha) * x1_old)
                            y1_ema = int(alpha * y1_new + (1 - alpha) * y1_old)
                            x2_ema = int(alpha * x2_new + (1 - alpha) * x2_old)
                            y2_ema = int(alpha * y2_new + (1 - alpha) * y2_old)
                            self._bbox_ema = (x1_ema, y1_ema, x2_ema, y2_ema, name, score)
        
        with self._state_lock:
            mode = self.drone_mode
            det = self._bbox_ema if self._bbox_ema is not None else self._bbox
        
        # ENHANCED: Controls manuels en mode MANUAL with maintien position
        if mode == DroneMode.MANUAL:
            # Apply altitude delta
            if self.manual_altitude_delta != 0.0:
                self.target_alt += self.manual_altitude_delta
                self.target_alt = max(0.5, min(5.0, self.target_alt))
            
            # PAS of stabilisation GPS - Vol libre comme le code C
            pitch_corr = 0.0
            yaw_corr = 0.0
        
        # MODE LOGIC (ORIGINALE)
        elif mode == DroneMode.RTH:
            if self.home_position:
                dx = self.home_position[0] - x
                dy = self.home_position[1] - y
                dist = math.sqrt(dx**2 + dy**2)
                
                if dist < 0.5:
                    self._cmd_land()
                else:
                    angle_to_home = math.atan2(dy, dx)
                    yaw_error = angle_to_home - yaw
                    yaw_corr = 0.3 * yaw_error
                    pitch_corr = -0.05  # 🔧 INVERTED for avancer vers home
        
        elif mode in [DroneMode.SEARCH, DroneMode.FOLLOW, DroneMode.ORBIT]:
            if det:
                # AUTO-SWITCH: Si en SEARCH and détection stable, passer en FOLLOW
                if mode == DroneMode.SEARCH:
                    with self._state_lock:
                        self.drone_mode = DroneMode.FOLLOW
                        mode = DroneMode.FOLLOW
                        self._yaw_override = 0.0  # 🆕 Stop immédiatement la rotation
                    self._ring(logging.INFO, "🎯 Target acquired - Switching to FOLLOW mode")
                    self.action_logger.log_event("mode_change", {"mode": "follow", "reason": "auto_detection"})
                
                x1, y1, x2, y2, name, score = det
                cx = (x1 + x2) / 2.0
                size = max(x2 - x1, y2 - y1)
                
                # Calculate des dimensions du bbox
                bbox_width = x2 - x1
                bbox_height = y2 - y1
                bbox_percent = (bbox_width * bbox_height) / (self.cam_w * self.cam_h) * 100
                
                cx_target = self.cam_w / 2.0
                size_target = self.cam_w * 0.25
                
                if mode == DroneMode.ORBIT:
                    target_yaw_rate = self.ORBIT_SPEED
                    yaw_corr = self.K_YAW_RATE * (target_yaw_rate - yaw_rate)
                    # 🆕 Limitr la correction of rotation
                    yaw_corr = clamp(yaw_corr, -1.0, 1.0)
                    err_s = size_target - size
                    pitch_corr = -self.SZ_KP * err_s  # 🔧 INVERTED
                
                    # Code of remplacement for le mode FOLLOW - Tracking visuel actif
                    # À insérer at partir of la ligne 1162

                elif mode == DroneMode.FOLLOW:
                        # LOG 23-25: Follow mode active with target info
                        self.action_logger.log_event("follow_active", {
                            "target_center_x": round(cx, 1),
                            "target_center_y": round((y1 + y2) / 2, 1),
                            "bbox_width": round(bbox_width, 1),
                            "bbox_height": round(bbox_height, 1),
                            "bbox_percent": round(bbox_percent, 2)
                        })

                        # 🎯 ACTIVE VISUAL TRACKING - Keep object centered in camera

                        # Center of l'image cible
                        cx_target = self.cam_w / 2.0
                        cy_target = self.cam_h / 2.0

                        # Center of la bbox détectée
                        cy = (y1 + y2) / 2.0

                        # Calculate des errors (in pixels)
                        err_x = cx_target - cx  # Error horizontale
                        err_y = cy_target - cy  # Error verticale

                        # Normalization des errors (as screen ratio)
                        err_x_norm = err_x / self.cam_w  # -0.5 at +0.5
                        err_y_norm = err_y / self.cam_h  # -0.5 at +0.5

                        # 🔧 YAW CONTROL - Rotation to center horizontally
                        # Dead zone to avoid les oscillations
                        YAW_DEADZONE = 0.05  # 5% of screen

                        if abs(err_x_norm) < YAW_DEADZONE:
                            # Object well centered horizontally
                            yaw_corr = 0.0
                            self._yaw_override = 0.0
                        else:
                            # Object off-center - rotate to center it
                            # Gains for le contrôle yaw
                            KP_YAW = 1.2  # Proportional gain
                            KD_YAW = 0.3  # Derivative gain

                            # Calculate derivativee
                            if not hasattr(self, '_err_x_prev'):
                                self._err_x_prev = 0.0
                            derr_x = err_x_norm - self._err_x_prev
                            self._err_x_prev = err_x_norm

                            # Command yaw proportionnelle-dérivée
                            yaw_corr = KP_YAW * err_x_norm + KD_YAW * derr_x
                            yaw_corr = clamp(yaw_corr, -0.5, 0.5)  # Limitr la vitesse of rotation
                            self._yaw_override = yaw_corr

                            print(f"[FOLLOW] YAW recentering: err_x={err_x:.0f}px ({err_x_norm*100:.1f}%), yaw_corr={yaw_corr:.3f}")

                        # 🔧 CONTRÔLE ROLL - Déplacement lateral for centrer verticalement (optionnel)
                        # Note: On peut ausif ignorer l'error verticale and laisser le drone ajuster naturellement
                        roll_corr = 0.0  # Désenabled for more of stabilité

                        # Alternative: Enable vertical control
                        # ROLL_DEADZONE = 0.08
                        # if abs(err_y_norm) > ROLL_DEADZONE:
                        #     KP_ROLL = 0.3
                        #     roll_corr = -KP_ROLL * err_y_norm  # Negative because pitch inverted
                        #     roll_corr = clamp(roll_corr, -0.2, 0.2)

                        # 🔧 AJUSTEMENT ALTITUDE according to distance
                        if bbox_percent < 15:  # Object very far
                            self.target_alt = 1.50  # High altitude
                        elif bbox_percent < 25:  # Medium distance
                            self.target_alt = 1.35  # Medium altitude
                        else:  # Object close (>=25%)
                            self.target_alt = 1.20  # Low altitude

                        # 🔧 PITCH CONTROL - Maintain optimal distance
                        bbox_width = x2 - x1
                        bbox_height = y2 - y1
                        bbox_area = bbox_width * bbox_height
                        screen_area = self.cam_w * self.cam_h
                        bbox_percent = (bbox_area / screen_area) * 100

                        # Distance zones
                        ZONE_TOO_CLOSE = 50.0    # >50% = too close, back up
                        ZONE_OPTIMAL_MAX = 40.0  # 30-40% = optimal zone
                        ZONE_OPTIMAL_MIN = 30.0
                        ZONE_FAR = 20.0          # <20% = far, approach

                        # Calculate error of taille for la distance
                        err_s = size_target - size
                        derr_s = err_s - self._sz_prev
                        self._sz_prev = err_s

                        # Approach/retreat logic
                        if bbox_percent > ZONE_TOO_CLOSE:
                            # Too close - back up
                            pitch_corr = +0.20
                            print(f"[FOLLOW] TOO CLOSE ({bbox_percent:.1f}%) - Backing up")

                        elif bbox_percent > ZONE_OPTIMAL_MAX:
                            # Near limit - slow down
                            pitch_corr = +0.05
                            print(f"[FOLLOW] LIMIT ZONE ({bbox_percent:.1f}%) - Slowing down")

                        elif bbox_percent >= ZONE_OPTIMAL_MIN:
                            # Optimal zone - maintain
                            pitch_corr = 0.0  # No movement
                            print(f"[FOLLOW] ✅ OPTIMAL ZONE ({bbox_percent:.1f}%) - Centered={abs(err_x_norm*100):.1f}%")

                        elif bbox_percent > ZONE_FAR:
                            # A bit far - approach moderately
                            base_speed = self.SZ_KP * err_s
                            pitch_corr = max(-base_speed, -0.40)
                            print(f"[FOLLOW] Approach modérée ({bbox_percent:.1f}%)")

                        else:
                            # Very far - approach quickly
                            pitch_corr = -(self.SZ_KP * err_s + self.SZ_KD * derr_s)
                            pitch_corr = clamp(pitch_corr, -0.70, 0.30)
                            print(f"[FOLLOW] Approach rapide ({bbox_percent:.1f}%)")

                        # Detailed debug
                        if bbox_percent < 35 or abs(err_x_norm) > 0.1:
                            print(f"[FOLLOW DEBUG] bbox={bbox_percent:.1f}% | "
                                  f"err_x={err_x:.0f}px({err_x_norm*100:+.1f}%) | "
                                  f"yaw={yaw_corr:+.3f} | pitch={pitch_corr:+.3f}")

                        # Sécurité: arrêter if objet trop près du bord
                        MARGIN = 50
                        near_edge = (x1 < MARGIN or x2 > self.cam_w - MARGIN or 
                                    y1 < MARGIN or y2 > self.cam_h - MARGIN)

                        if near_edge and pitch_corr < 0:
                            pitch_corr = 0.0
                            print(f"[FOLLOW] ⚠️ SAFETY: Object near edge - Arrêt approche")

                else:  # SEARCH
                    err_x = cx_target - cx
                    
                    # 🆕 ZONE MORTE to avoid oscillations
                    if abs(err_x) < self.YAW_DEADZONE:
                        err_x = 0.0
                        yaw_corr = 0.0
                    else:
                        derr_x = err_x - self._cx_prev
                        yaw_corr = self.CX_KP * err_x + self.CX_KD * derr_x
                        yaw_corr = clamp(yaw_corr, -0.4, 0.4)  # RÉDUIT: ±0.6 → ±0.4
                    
                    self._cx_prev = err_x
                    
                    err_s = size_target - size
                    derr_s = err_s - self._sz_prev
                    self._sz_prev = err_s
                    pitch_corr = -(self.SZ_KP * err_s + self.SZ_KD * derr_s)  # 🔧 INVERTED
                    
                    threshold_x = 20
                    threshold_s = 30
                    
                    if abs(err_x) < threshold_x and abs(err_s) < threshold_s:
                        yaw_corr = 0.0
                        pitch_corr = 0.0
                        self._yaw_override = 0.0
                    else:
                        pitch_corr = clamp(pitch_corr, -0.11, 0.11)
                        self._yaw_override = yaw_corr
            else:
                if mode == DroneMode.SEARCH:
                    target_rate = self.sweep_rate_adjustable  # Utiliser la vitesse réglable
                    # 🆕 RÉDUIT: ±5.0 → ±1.5 for rotation more douce
                    self._yaw_override = clamp(self.K_YAW_RATE * (target_rate - yaw_rate), -1.5, 1.5)
                else:
                    self._yaw_override = 0.0
        
        # Apply corrections UNIQUEMENT if pas en mode MANUAL
        if mode != DroneMode.MANUAL:
            pitch_input += pitch_corr
        yaw_input = self._yaw_override if mode != DroneMode.RTH else yaw_corr
        
        # LOG 13: Commands of contrôle calculées (CRITIQUE!)
        self.action_logger.log_event("control_commands", {
            "pitch_corr": round(pitch_corr, 4),
            "yaw_corr": round(yaw_corr, 4),
            "pitch_input": round(pitch_input, 4),
            "yaw_input": round(yaw_input, 4),
            "roll_input": round(roll_input, 4),
            "vertical_input": round(vertical_input, 4),
            "mode": mode.value
        })
        
        # Motor commands (FORMULES ORIGINALES)
        fl = self.K_VERTICAL_THRUST + vertical_input - roll_input + pitch_input - yaw_input
        fr = -(self.K_VERTICAL_THRUST + vertical_input + roll_input + pitch_input + yaw_input)
        rl = -(self.K_VERTICAL_THRUST + vertical_input - roll_input - pitch_input + yaw_input)
        rr = self.K_VERTICAL_THRUST + vertical_input + roll_input - pitch_input - yaw_input
        
        self.motors['front_left'].setVelocity(fl)
        self.motors['front_right'].setVelocity(fr)
        self.motors['rear_left'].setVelocity(rl)
        self.motors['rear_right'].setVelocity(rr)
        
        # LOG 14: Speeds moteurs (CRITIQUE!)
        self.action_logger.log_event("motor_velocities", {
            "front_left": round(fl, 2),
            "front_right": round(fr, 2),
            "rear_left": round(rl, 2),
            "rear_right": round(rr, 2)
        })
        
        # Recording vidéo
        if self.video_recorder:
            frame = self.get_camera_bgr()
            if frame is not None:
                annotated = self._annotate_frame(frame, self._bbox)
                self.video_recorder.write(annotated)
        
        # Mesure FPS (VERSION ORIGINALE)
        t1 = time.time()
        self._det_times.append(t1 - t0)
    
    def _annotate_frame(self, img, bbox=None):
        """Annote l'image avec les infos"""
        img = img.copy()
        
        # Texte of recherche
        label = None
        if self.search_target:
            label = "Searching: {}".format(self.search_target)
        
        is_tracking = self.hybrid_tracker and self.hybrid_tracker.tracking_active
        mode = self.drone_mode
        
        if label:
            cv2.putText(img, label, (10, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 140, 255), 2)
        
        # ENHANCED: Bbox with labels compacts AUTOUR du cadre
        if bbox:
            x1, y1, x2, y2, name, score = bbox
            
            # Couleur according to mode
            if is_tracking:
                box_color = (0, 255, 255)  # Jaune for tracking
                box_label = "TRK"  # Plus court
            else:
                box_color = (0, 255, 0)  # Vert for detection
                box_label = "DET"  # Plus court
            
            # Cadre principal épais
            thickness = 3
            cv2.rectangle(img, (x1, y1), (x2, y2), box_color, thickness)
            
            # Coins renforcés (style moderne)
            corner_length = 15  # Réduit of 20 at 15
            corner_thickness = 3  # Réduit of 4 at 3
            
            # Coin haut-gauche
            cv2.line(img, (x1, y1), (x1 + corner_length, y1), box_color, corner_thickness)
            cv2.line(img, (x1, y1), (x1, y1 + corner_length), box_color, corner_thickness)
            
            # Coin haut-droit
            cv2.line(img, (x2, y1), (x2 - corner_length, y1), box_color, corner_thickness)
            cv2.line(img, (x2, y1), (x2, y1 + corner_length), box_color, corner_thickness)
            
            # Coin bas-gauche
            cv2.line(img, (x1, y2), (x1 + corner_length, y2), box_color, corner_thickness)
            cv2.line(img, (x1, y2), (x1, y2 - corner_length), box_color, corner_thickness)
            
            # Coin bas-droit
            cv2.line(img, (x2, y2), (x2 - corner_length, y2), box_color, corner_thickness)
            cv2.line(img, (x2, y2), (x2, y2 - corner_length), box_color, corner_thickness)
            
            # Labels COMPACTS autour du cadre (pas dessus)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.45  # RÉDUIT of 0.7 at 0.45
            font_thickness = 1  # RÉDUIT of 2 at 1
            padding = 3  # RÉDUIT of 5 at 3
            
            # Label 1: Nom (en haut at gauche, AU-DESSUS du cadre)
            name_text = name.upper()
            (name_w, name_h), _ = cv2.getTextSize(name_text, font, font_scale, font_thickness)
            
            name_x = x1
            name_y = y1 - 8  # AU-DESSUS du cadre
            
            # Si pas assez d'espace en haut, mettre en bas
            if name_y - name_h - padding < 0:
                name_y = y2 + name_h + 8  # EN-DESSOUS du cadre
            
            # Fond semi-transparent for le nom
            cv2.rectangle(img,
                         (name_x - padding, name_y - name_h - padding),
                         (name_x + name_w + padding, name_y + padding),
                         box_color, -1)
            
            cv2.putText(img, name_text,
                       (name_x, name_y),
                       font, font_scale, (0, 0, 0), font_thickness)
            
            # Label 2: Confidence (en haut at droite, AU-DESSUS du cadre)
            conf_text = "{:.0%}".format(score)  # Format court: "67%"
            (conf_w, conf_h), _ = cv2.getTextSize(conf_text, font, font_scale, font_thickness)
            
            conf_x = x2 - conf_w
            conf_y = y1 - 8  # AU-DESSUS du cadre
            
            # Si pas assez d'espace en haut, mettre en bas
            if conf_y - conf_h - padding < 0:
                conf_y = y2 + conf_h + 8  # EN-DESSOUS du cadre
            
            # Fond for la confidence
            cv2.rectangle(img,
                         (conf_x - padding, conf_y - conf_h - padding),
                         (conf_x + conf_w + padding, conf_y + padding),
                         box_color, -1)
            
            cv2.putText(img, conf_text,
                       (conf_x, conf_y),
                       font, font_scale, (0, 0, 0), font_thickness)
            
            # Label 3: Statut (petit badge en bas at droite, SUR le coin du cadre)
            status_text = box_label
            status_scale = 0.35  # Encore more petit
            (status_w, status_h), _ = cv2.getTextSize(status_text, font, status_scale, font_thickness)
            
            status_x = x2 - status_w - 4
            status_y = y2 - 4
            
            # Fond du badge
            cv2.rectangle(img,
                         (status_x - 2, status_y - status_h - 2),
                         (status_x + status_w + 2, status_y + 2),
                         box_color, -1)
            
            cv2.putText(img, status_text,
                       (status_x, status_y),
                       font, status_scale, (0, 0, 0), font_thickness)
        
        # Mode & FPS
        mode_text = "TRACKING" if is_tracking else "DETECTING"
        if mode == DroneMode.FOLLOW:
            mode_text = "FOLLOW"
        elif mode == DroneMode.ORBIT:
            mode_text = "ORBIT"
        elif mode == DroneMode.RTH:
            mode_text = "RTH"
        
        fps_text = "FPS: {:.0f} | {}".format(self.det_fps(), mode_text)
        cv2.putText(img, fps_text, (10, self.cam_h-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Batterie
        bat_pct = self.battery.get_percentage()
        bat_color = (0, 255, 0) if bat_pct > 30 else (0, 165, 255) if bat_pct > 20 else (0, 0, 255)
        cv2.putText(img, "BAT: {:.0f}%".format(bat_pct), (self.cam_w - 120, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, bat_color, 2)
        
        # Recording indicator
        if self.video_recorder:
            cv2.circle(img, (self.cam_w - 30, self.cam_h - 30), 10, (0, 0, 255), -1)
        
        return img
    
    def _start_ui(self):
        """Interface web complète"""
        app = Flask(__name__)
        
        def gen_mjpeg():
            """Générateur MJPEG (VERSION ORIGINALE QUI FONCTIONNAIT)"""
            while not self._shutdown:
                try:
                    frm = self.get_camera_bgr()
                    if frm is None:
                        time.sleep(0.02)
                        continue
                    
                    # CRITICAL FIX: Passer la bbox actuelle for l'affichage
                    with self._state_lock:
                        current_bbox = self._bbox_ema if self._bbox_ema is not None else self._bbox
                    
                    frm = self._annotate_frame(frm, bbox=current_bbox)
                    ok, buf = cv2.imencode(".jpg", frm)
                    if ok:
                        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
                except Exception:
                    time.sleep(0.02)
                    continue
        
        @app.route("/video_feed")
        def video_feed():
            """Route vidéo (VERSION ORIGINALE SIMPLIFIÉE)"""
            return Response(gen_mjpeg(), mimetype="multipart/x-mixed-replace; boundary=frame")
        
        @app.route("/")
        def index():
            html = """
<!DOCTYPE html>
<html>
<head>
<title>🚁 Ultimate Drone Controller</title>
<meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0e14; color: #e8eef5; }
.container { max-width: 100%; margin: 0; padding: 0; }

/* COCKPIT LAYOUT: Top bar */
.top-bar {
    background: linear-gradient(135deg, #1e2430, #2d3748);
    padding: 15px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #3b4252;
    box-shadow: 0 2px 10px rgba(0,0,0,0.5);
}
.top-bar-left {
    display: flex;
    gap: 10px;
    align-items: center;
}
.top-bar-center {
    display: flex;
    gap: 20px;
    align-items: center;
    font-size: 16px;
    font-weight: bold;
}
.mode-display {
    background: #13b26b;
    padding: 8px 20px;
    border-radius: 20px;
    font-size: 14px;
    letter-spacing: 1px;
}
.fps-display {
    color: #88c0d0;
}

/* COCKPIT LAYOUT: Main grid 3 colonnes */
.cockpit-grid {
    display: grid;
    grid-template-columns: 350px 1fr 350px;
    height: calc(100vh - 80px);
    gap: 0;
}

/* Left column: Telemetry */
.telemetry-panel {
    background: #1e2430;
    padding: 20px;
    overflow-y: auto;
    border-right: 2px solid #0a0e14;
}

/* Center column: Video */
.video-panel-center {
    background: #0f1726;
    display: flex;
    flex-direction: column;
    position: relative;
}
.video-panel-center img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

/* Right column: Mission & Navigation */
.mission-panel {
    background: #1e2430;
    padding: 20px;
    overflow-y: auto;
    border-left: 2px solid #0a0e14;
}

/* Barre inférieure: Controls clavier & Logs */
.bottom-bar {
    display: grid;
    grid-template-columns: 350px 1fr 350px;
    background: #1e2430;
    border-top: 2px solid #3b4252;
    height: 180px;
}
.keyboard-panel {
    padding: 15px;
    border-right: 2px solid #0a0e14;
}
.logs-panel {
    padding: 15px;
    border-left: 2px solid #0a0e14;
}

/* Sections */
.section {
    margin-bottom: 25px;
}
.section-title {
    font-size: 14px;
    color: #88c0d0;
    margin-bottom: 12px;
    font-weight: bold;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Boutons */
.btn { border: none; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 13px; transition: all 0.2s; }
.btn:hover { transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
.btn-primary { background: #13b26b; color: #fff; }
.btn-danger { background: #e23d3d; color: #fff; }
.btn-warning { background: #ffc13a; color: #000; }
.btn-info { background: #4a9eff; color: #fff; }
.btn-secondary { background: #6c757d; color: #fff; }
.btn-small { padding: 8px 14px; font-size: 12px; }

/* Stats télémétrie */
.stat-item {
    background: #0f1726;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.stat-label {
    font-size: 13px;
    color: #88c0d0;
}
.stat-value {
    font-size: 18px;
    font-weight: bold;
    color: #13b26b;
}

/* Search */
.search-box {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.search-box input {
    padding: 10px;
    border-radius: 6px;
    border: 1px solid #3b4252;
    background: #0f1726;
    color: #fff;
    font-size: 13px;
}
.search-buttons {
    display: flex;
    gap: 8px;
}

/* Modes */
.modes-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}

/* GPS Mini */
.map-mini {
    width: 100%;
    height: 180px;
    background: #0f1726;
    border-radius: 8px;
    position: relative;
    overflow: hidden;
}

/* Logs */
.logs {
    background: #0f1726;
    padding: 10px;
    border-radius: 8px;
    height: 140px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 11px;
}
.log-line { padding: 2px 0; }

/* Badges */
.badge { display: inline-block; padding: 4px 10px; border-radius: 10px; font-size: 11px; font-weight: bold; margin-left: 8px; }
.badge-success { background: #13b26b; color: #fff; }
.badge-danger { background: #e23d3d; color: #fff; }
.badge-warning { background: #ffc13a; color: #000; }

/* 🆕 Styles pour les filtres d'événements */
#event-filters input[type="checkbox"] {
    accent-color: #13b26b;
}
#event-filters::-webkit-scrollbar {
    width: 6px;
}
#event-filters::-webkit-scrollbar-track {
    background: #0f1726;
    border-radius: 3px;
}
#event-filters::-webkit-scrollbar-thumb {
    background: #3b4252;
    border-radius: 3px;
}
#event-filters::-webkit-scrollbar-thumb:hover {
    background: #4c566a;
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

/* ENHANCED: Sliders verticaux (style avion/Windows) */
.gauges-container {
    display: flex;
    gap: 15px;
    margin-top: 10px;
    justify-content: space-around;
}
.slider-control {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.slider-label {
    font-size: 11px;
    color: #88c0d0;
    margin-bottom: 10px;
    font-weight: bold;
    text-align: center;
}
.slider-container {
    position: relative;
    width: 50px;
    height: 200px;
    background: #0f1726;
    border-radius: 25px;
    padding: 10px 0;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
}
.slider-track {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    width: 8px;
    height: calc(100% - 20px);
    top: 10px;
    background: #2d3648;
    border-radius: 4px;
}
.slider-fill {
    position: absolute;
    bottom: 0;
    width: 100%;
    background: linear-gradient(to top, #13b26b, #4a9eff);
    border-radius: 4px;
    transition: height 0.1s ease;
}
.slider-thumb {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    width: 35px;
    height: 35px;
    background: linear-gradient(135deg, #e8eef5, #c0c8d0);
    border: 3px solid #3b4252;
    border-radius: 50%;
    cursor: grab;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    transition: box-shadow 0.2s;
}
.slider-thumb:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.6);
}
.slider-thumb:active {
    cursor: grabbing;
    box-shadow: 0 2px 4px rgba(0,0,0,0.4);
}
.slider-value {
    margin-top: 10px;
    font-size: 16px;
    font-weight: bold;
    color: #13b26b;
    text-align: center;
}
.slider-minmax {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 200px;
    margin-left: 8px;
    font-size: 10px;
    color: #6c757d;
}
.slider-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
}

/* ENHANCED: Controls clavier */
.keyboard-controls {
    background: #0f1726;
    padding: 15px;
    border-radius: 8px;
    margin-top: 15px;
}
.keyboard-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 10px;
}
.key-hint {
    background: #1e2430;
    padding: 10px;
    border-radius: 6px;
    text-align: center;
    border: 2px solid transparent;
    transition: all 0.2s;
}
.key-hint.active {
    border-color: #13b26b;
    background: #13b26b22;
}
.key-name {
    font-size: 18px;
    font-weight: bold;
    color: #ffc13a;
    display: block;
    margin-bottom: 5px;
}
.key-action {
    font-size: 11px;
    color: #88c0d0;
}
</style>
</head>
<body>
<div class="container">
  <!-- COCKPIT LAYOUT: Top bar -->
  <div class="top-bar">
    <div class="top-bar-left">
      <button class="btn btn-primary" onclick="sendAction('takeoff')">🛫 Take-Off</button>
      <button class="btn btn-danger" onclick="sendAction('land')">🛬 Land</button>
      <button class="btn btn-danger" onclick="sendAction('emergency')">🚨 Emergency</button>
      <button class="btn btn-warning" onclick="sendAction('rth')">🏠 RTH</button>
      <button class="btn" onclick="downloadLogs()" style="background: #9333ea; color: white;">📊 Download Logs</button>
    </div>
    <div class="top-bar-center">
      <div class="mode-display" id="mode-display">MODE: MANUAL</div>
      <div class="fps-display" id="fps-display">28 FPS</div>
    </div>
  </div>
  
  <!-- COCKPIT LAYOUT: Main grid 3 colonnes -->
  <div class="cockpit-grid">
    <!-- COLONNE GAUCHE: Telemetry -->
    <div class="telemetry-panel">
      <div class="section">
        <div class="section-title">📊 TÉLÉMÉTRIE</div>
        
        <div class="stat-item">
          <span class="stat-label">Altitude</span>
          <span class="stat-value" id="altitude">0.0m</span>
        </div>
        
        <div class="stat-item">
          <span class="stat-label">Batterie</span>
          <span class="stat-value" id="battery">100%</span>
        </div>
        
        <div class="stat-item">
          <span class="stat-label">Speed</span>
          <span class="stat-value" id="speed">0.0m/s</span>
        </div>
      </div>
      
      <div class="section">
        <div class="section-title">🎚️ CONTRÔLES</div>
        
        <div class="gauges-container">
          <!-- Slider vitesse de rotation -->
          <div class="slider-control">
            <div class="slider-label">⟳ ROTATION</div>
            <div class="slider-wrapper">
              <div class="slider-container">
                <div class="slider-track">
                  <div class="slider-fill" id="rotation-fill" style="height: 50%;"></div>
                </div>
                <div class="slider-thumb" id="rotation-thumb" style="bottom: calc(50% - 17.5px);"></div>
              </div>
              <div class="slider-minmax">
                <span>90</span>
                <span>45</span>
                <span>0</span>
              </div>
            </div>
            <div class="slider-value" id="rotation-value">45</div>
          </div>
          
          <!-- Slider altitude -->
          <div class="slider-control">
            <div class="slider-label">⬆ ALTITUDE</div>
            <div class="slider-wrapper">
              <div class="slider-container">
                <div class="slider-track">
                  <div class="slider-fill" id="altitude-fill" style="height: 22%;"></div>
                </div>
                <div class="slider-thumb" id="altitude-thumb" style="bottom: calc(22% - 17.5px);"></div>
              </div>
              <div class="slider-minmax">
                <span>5.0</span>
                <span>2.8</span>
                <span>0.5</span>
              </div>
            </div>
            <div class="slider-value" id="altitude-value">1.5</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- CENTER COLUMN: Video -->
    <div class="video-panel-center">
      <img src="/video_feed" id="video-feed" alt="Drone Camera Feed">
    </div>
    
    <!-- COLONNE DROITE: Mission & Navigation -->
    <div class="mission-panel">
      <div class="section">
        <div class="section-title">🔍 SEARCH</div>
        
        <div class="search-box">
          <input type="text" id="search-input" placeholder='Objet (ex: "car", "person")'>
          <div class="search-buttons">
            <button class="btn btn-primary btn-small" onclick="doSearch()">🔍 Search</button>
            <button class="btn btn-warning btn-small" onclick="sendAction('stop')">⏹ Stop</button>
          </div>
        </div>
      </div>
      
      <div class="section">
        <div class="section-title">🎯 AUTONOMOUS MODES</div>
        
        <div class="modes-grid">
          <button class="btn btn-info btn-small" onclick="sendAction('follow')">🎯 Follow</button>
          <button class="btn btn-info btn-small" onclick="sendAction('orbit')">🔄 Orbit</button>
          <button class="btn btn-secondary btn-small" onclick="sendAction('manual')">✋ Manual</button>
          <button class="btn btn-warning btn-small" onclick="sendAction('rth')">🏠 RTH</button>
        </div>
      </div>
      
      <div class="section">
        <div class="section-title">🗺️ GPS TRACK</div>
        <canvas id="map" class="map-mini"></canvas>
      </div>
      
      <div class="section">
        <div class="section-title">📸 RECORDING</div>
        <div class="search-buttons">
          <button class="btn btn-info btn-small" onclick="sendAction('photo')">📸 Photo</button>
          <button class="btn btn-danger btn-small" onclick="sendAction('record')" id="rec-btn">🔴 Rec</button>
        </div>
      </div>
      
      <!-- 🆕 SECTION FILTRAGE DES ÉVÉNEMENTS -->
      <div class="section">
        <div class="section-title">📋 LOGGING FILTERS</div>
        <div style="display: flex; gap: 5px; margin-bottom: 8px;">
          <button class="btn btn-small" onclick="toggleAllFilters(true)" style="flex: 1; padding: 4px; font-size: 11px; background: #13b26b;">✅ Check all</button>
          <button class="btn btn-small" onclick="toggleAllFilters(false)" style="flex: 1; padding: 4px; font-size: 11px; background: #dc2626;">❌ Uncheck all</button>
        </div>
        <div id="event-filters" style="max-height: 200px; overflow-y: auto; font-size: 11px;">
          <!-- Chargé dynamiquement via JavaScript -->
        </div>
      </div>
    </div>
  </div>
  
  <!-- BARRE INFÉRIEURE: Controls clavier & Logs -->
  <div class="bottom-bar">
    <div class="keyboard-panel">
      <div class="keyboard-controls" id="keyboard-controls" style="display:none;">
        <div class="section-title">⌨️ CONTRÔLES CLAVIER</div>
        <div class="keyboard-grid">
          <div></div>
          <div class="key-hint" id="key-z">
            <span class="key-name">Z</span>
            <span class="key-action">Forward</span>
          </div>
          <div></div>
          
          <div class="key-hint" id="key-q">
            <span class="key-name">Q</span>
            <span class="key-action">Rotatesr ←</span>
          </div>
          <div class="key-hint" id="key-s">
            <span class="key-name">S</span>
            <span class="key-action">Backward</span>
          </div>
          <div class="key-hint" id="key-d">
            <span class="key-name">D</span>
            <span class="key-action">Rotatesr →</span>
          </div>
          
          <div class="key-hint" id="key-a">
            <span class="key-name">A</span>
            <span class="key-action">Down</span>
          </div>
          <div></div>
          <div class="key-hint" id="key-e">
            <span class="key-name">E</span>
            <span class="key-action">Up</span>
          </div>
        </div>
      </div>
    </div>
    
    <div style="border-left: 2px solid #0a0e14; border-right: 2px solid #0a0e14;"></div>
    
    <div class="logs-panel">
      <div class="section-title">📜 LOGS</div>
      <div class="logs" id="logs">Loading...</div>
    </div>
  </div>
</div>

<script>
function sendAction(cmd) {
  console.log('Sending action:', cmd);
  fetch('/action', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'action=' + cmd
  }).then(r => r.json())
    .then(data => {
      console.log('Action response:', data);
      updateStatus();
    })
    .catch(err => console.error('Action error:', err));
}

function doSearch() {
  const query = document.getElementById('search-input').value;
  if (!query) {
    alert('Please enter a search term');
    return;
  }
  console.log('Searching for:', query);
  fetch('/search', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'query=' + encodeURIComponent(query)
  }).then(r => r.json())
    .then(data => {
      console.log('Search response:', data);
      updateStatus();
    })
    .catch(err => console.error('Search error:', err));
}

function updateStatus() {
  fetch('/status')
    .then(r => r.json())
    .then(data => {
      document.getElementById('altitude').textContent = data.altitude + 'm';
      document.getElementById('battery').textContent = data.battery + '%';
      document.getElementById('speed').textContent = data.speed + 'm/s';
      document.getElementById('mode-display').textContent = 'MODE: ' + data.mode;
      document.getElementById('fps-display').textContent = data.fps + ' FPS';
      
      // Battery color
      const batEl = document.getElementById('battery');
      if (data.battery < 20) batEl.style.color = '#e23d3d';
      else if (data.battery < 30) batEl.style.color = '#ffc13a';
      else batEl.style.color = '#13b26b';
      
      // Logs
      const logsEl = document.getElementById('logs');
      logsEl.innerHTML = data.logs.map(l => '<div class="log-line">' + l + '</div>').join('');
      logsEl.scrollTop = logsEl.scrollHeight;
      
      // GPS trace
      drawMap(data.gps_trace);
      
      // ENHANCED: Update viifbilité controls clavier
      updateControlsViifbility(data.mode);
    })
    .catch(err => console.error('Status error:', err));
}

function drawMap(trace) {
  const canvas = document.getElementById('map');
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
  
  ctx.fillStyle = '#0f1726';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  if (trace.length < 2) return;
  
  // Échelle
  const xs = trace.map(p => p[0]);
  const ys = trace.map(p => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;
  const scale = Math.min(canvas.width / rangeX, canvas.height / rangeY) * 0.8;
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  
  // Trace
  ctx.strokeStyle = '#4a9eff';
  ctx.lineWidth = 2;
  ctx.beginPath();
  trace.forEach((p, i) => {
    const x = centerX + (p[0] - (minX + maxX) / 2) * scale;
    const y = centerY - (p[1] - (minY + maxY) / 2) * scale;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  
  // Current position
  if (trace.length > 0) {
    const last = trace[trace.length - 1];
    const x = centerX + (last[0] - (minX + maxX) / 2) * scale;
    const y = centerY - (last[1] - (minY + maxY) / 2) * scale;
    ctx.fillStyle = '#e23d3d';
    ctx.beginPath();
    ctx.arc(x, y, 6, 0, 2 * Math.PI);
    ctx.fill();
  }
  
  // Home
  if (trace.length > 0) {
    const home = trace[0];
    const x = centerX + (home[0] - (minX + maxX) / 2) * scale;
    const y = centerY - (home[1] - (minY + maxY) / 2) * scale;
    ctx.fillStyle = '#13b26b';
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, 2 * Math.PI);
    ctx.fill();
  }
}

setInterval(updateStatus, 1000);
updateStatus();

// ============================================================================
// ENHANCED: SLIDERS VERTICAUX (style avion/Windows)
// ============================================================================

let rotationSpeed = 45;
let targetAltitude = 1.5;

function initSliders() {
    const rotationThumb = document.getElementById('rotation-thumb');
    const rotationFill = document.getElementById('rotation-fill');
    const rotationValue = document.getElementById('rotation-value');
    
    const altitudeThumb = document.getElementById('altitude-thumb');
    const altitudeFill = document.getElementById('altitude-fill');
    const altitudeValue = document.getElementById('altitude-value');
    
    // Fonction pour mettre à jour un slider
    function updateSlider(thumb, fill, valueElem, percentage, getValue, sendValue) {
        const clampedPercentage = Math.max(0, Math.min(100, percentage));
        thumb.style.bottom = 'calc(' + clampedPercentage + '% - 20px)';
        fill.style.height = clampedPercentage + '%';
        const value = getValue(clampedPercentage);
        valueElem.textContent = value;
        if (sendValue) sendValue(value);
    }
    
    // Percentage conversion vers valeur pour rotation (0-90°/s)
    function percentToRotation(percent) {
        return Math.round((percent / 100) * 90);
    }
    
    // Percentage conversion vers valeur pour altitude (0.5-5.0m)
    function percentToAltitude(percent) {
        return ((percent / 100) * 4.5 + 0.5).toFixed(1);
    }
    
    // Gestion du drag pour rotation
    let isDraggingRotation = false;
    rotationThumb.addEventListener('mousedown', function(e) {
        isDraggingRotation = true;
        e.preventDefault();
    });
    
    // Gestion du drag pour altitude
    let isDraggingAltitude = false;
    altitudeThumb.addEventListener('mousedown', function(e) {
        isDraggingAltitude = true;
        e.preventDefault();
    });
    
    // Gestion du mouvement de la souris
    document.addEventListener('mousemove', function(e) {
        if (isDraggingRotation) {
            const container = rotationThumb.parentElement;
            const rect = container.getBoundingClientRect();
            const y = e.clientY - rect.top;
            const height = rect.height - 20; // Enlever padding
            const percentage = ((height - y + 10) / height) * 100;
            
            updateSlider(
                rotationThumb, rotationFill, rotationValue,
                percentage, percentToRotation,
                function(val) {
                    rotationSpeed = val;
                    fetch('/set_rotation_speed', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({speed: val})
                    });
                }
            );
        }
        
        if (isDraggingAltitude) {
            const container = altitudeThumb.parentElement;
            const rect = container.getBoundingClientRect();
            const y = e.clientY - rect.top;
            const height = rect.height - 20;
            const percentage = ((height - y + 10) / height) * 100;
            
            updateSlider(
                altitudeThumb, altitudeFill, altitudeValue,
                percentage, percentToAltitude,
                function(val) {
                    targetAltitude = parseFloat(val);
                    fetch('/set_target_altitude', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({altitude: parseFloat(val)})
                    });
                }
            );
        }
    });
    
    // Relâchement de la souris
    document.addEventListener('mouseup', function() {
        isDraggingRotation = false;
        isDraggingAltitude = false;
    });
}

// ============================================================================
// ENHANCED: CONTRÔLES CLAVIER
// ============================================================================

let keyboardEnabled = false;
let keysPressed = {};

function initKeyboardControls() {
    document.addEventListener('keydown', function(e) {
        if (!keyboardEnabled) return;
        
        const key = e.key.toLowerCase();
        if (keysPressed[key]) return;
        
        keysPressed[key] = true;
        
        const keyElem = document.getElementById('key-' + key);
        if (keyElem) keyElem.classList.add('active');
        
        fetch('/manual_control', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({key: key, action: 'press'})
        });
    });
    
    document.addEventListener('keyup', function(e) {
        if (!keyboardEnabled) return;
        
        const key = e.key.toLowerCase();
        keysPressed[key] = false;
        
        const keyElem = document.getElementById('key-' + key);
        if (keyElem) keyElem.classList.remove('active');
        
        fetch('/manual_control', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({key: key, action: 'release'})
        });
    });
}

function updateControlsViifbility(mode) {
    const keyboardControls = document.getElementById('keyboard-controls');
    if (mode === 'MANUAL') {
        keyboardControls.style.display = 'block';
        keyboardEnabled = true;
    } else {
        keyboardControls.style.display = 'none';
        keyboardEnabled = false;
        keysPressed = {};
    }
}

// Initialize on load
window.addEventListener('load', function() {
    initSliders();
    initKeyboardControls();
    loadEventFilters();  // 🆕 Load les filtres au démarrage
});

// 🆕 GESTION DES FILTRES D'ÉVÉNEMENTS
function loadEventFilters() {
    fetch('/get_event_filters')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                displayEventFilters(data.filters);
            }
        })
        .catch(error => console.error('Error chargement filtres:', error));
}

function displayEventFilters(filters) {
    const container = document.getElementById('event-filters');
    if (!container) return;
    
    // Icons for each event type
    const icons = {
        'takeoff': '🛫',
        'land': '🛬',
        'emergency': '🚨',
        'detection': '🔍',
        'velocity': '⚡',
        'position': '📍',
        'mode_change': '🔄',
        'tracking': '🎯',
        'command': '🎮',
        'photo': '📸',
        'video': '🎥',
        'waypoint': '🗺️',
        'geofence': '🚧',
        'battery': '🔋',
        'imu_data': '📐',
        'altitude_control': '📏',
        'control_commands': '🎛️',
        'motor_velocities': '⚙️',
        'follow_active': '👁️',
        'other': '📄'
    };
    
    // Labels in English
    const labels = {
        'takeoff': 'Takeoff',
        'land': 'Landing',
        'emergency': 'Emergency',
        'detection': 'Detection',
        'velocity': 'Speed',
        'position': 'Position',
        'mode_change': 'Mode change',
        'tracking': 'Tracking',
        'command': 'Commands',
        'photo': 'Photos',
        'video': 'Video',
        'waypoint': 'Waypoints',
        'geofence': 'Geofence',
        'battery': 'Battery',
        'imu_data': 'IMU Data',
        'altitude_control': 'Altitude Ctrl',
        'control_commands': 'Control Cmds',
        'motor_velocities': 'Motor Speeds',
        'follow_active': 'Follow State',
        'other': 'Others'
    };
    
    let html = '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">';
    
    for (const [eventType, enabled] of Object.entries(filters)) {
        const icon = icons[eventType] || '📄';
        const label = labels[eventType] || eventType;
        const checkedAttr = enabled ? 'checked' : '';
        
        html += `
            <label style="display: flex; align-items: center; padding: 3px; cursor: pointer; background: ${enabled ? '#0a3d2a' : '#1a1d29'}; border-radius: 4px; transition: background 0.2s;" 
                   onmouseover="this.style.background='${enabled ? '#0d5038' : '#252935'}'" 
                   onmouseout="this.style.background='${enabled ? '#0a3d2a' : '#1a1d29'}'">
                <input type="checkbox" 
                       ${checkedAttr} 
                       onchange="toggleEventFilter('${eventType}', this.checked)"
                       style="margin-right: 6px; cursor: pointer;">
                <span style="font-size: 12px;">${icon} ${label}</span>
            </label>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function toggleEventFilter(eventType, enabled) {
    fetch('/set_event_filter', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({event_type: eventType, enabled: enabled})
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            // Visual update immédiate
            const container = document.getElementById('event-filters');
            const label = container.querySelector(`input[onchange*="${eventType}"]`).parentElement;
            label.style.background = enabled ? '#0a3d2a' : '#1a1d29';
            
            console.log(`✅ Filter "${eventType}" ${enabled ? 'enabled' : 'désenabled'}`);
        } else {
            console.error('Error:', data.message);
        }
    })
    .catch(error => console.error('Error toggle filtre:', error));
}


function toggleAllFilters(enabled) {
    fetch('/get_event_filters')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                const filters = data.filters;
                let promises = [];
                
                for (const eventType in filters) {
                    promises.push(
                        fetch('/set_event_filter', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({event_type: eventType, enabled: enabled})
                        })
                    );
                }
                
                Promise.all(promises).then(() => {
                    loadEventFilters();
                    console.log(`✅ Tous les filtres ${enabled ? 'enableds' : 'désenableds'}`);
                });
            }
        })
        .catch(error => console.error('Error toggle all:', error));
}

function downloadLogs() { if (confirm("Télécharger les logs?")) window.location.href = "/download_logs"; }
</script>
</body>
</html>
"""
            return html
        
        @app.route("/action", methods=["POST"])
        def action():
            act = request.form.get("action", "")
            if act == "takeoff":
                self._cmd_takeoff()
            elif act == "land":
                self._cmd_land()
            elif act == "emergency":
                self._cmd_emergency_stop()
            elif act == "rth":
                self._cmd_return_home()
            elif act == "stop":
                self._cmd_stop_search()
            elif act == "follow":
                self._cmd_follow_mode()
            elif act == "orbit":
                self._cmd_orbit_mode()
            elif act == "manual":
                with self._state_lock:
                    self.drone_mode = DroneMode.MANUAL
            elif act == "photo":
                self.take_photo()
            elif act == "record":
                if self.video_recorder:
                    self._cmd_stop_recording()
                else:
                    self._cmd_start_recording()
            return jsonify({"status": "ok"})
        
        @app.route("/search", methods=["POST"])
        def search():
            query = request.form.get("query", "").strip()
            if query:
                self._cmd_start_search(query)
            return jsonify({"status": "ok"})
        
        @app.route("/status")
        def status():
            def compute_status():
                try:
                    x, y, z = self.gps.getValues()
                    speed = 0.0
                    if len(self._gps_trace) >= 2:
                        p1 = self._gps_trace[-1]
                        p2 = self._gps_trace[-2]
                        dt = p1[2] - p2[2]
                        if dt > 0:
                            dist = distance_2d((p1[0], p1[1]), (p2[0], p2[1]))
                            speed = dist / dt
                            
                            # LOG 19, 34: Velocity
                            self.action_logger.log_event("velocity", {"speed": round(speed, 3)})
                    
                    return {
                        "altitude": round(z, 2),
                        "battery": int(self.battery.get_percentage()),
                        "speed": round(speed, 2),
                        "mode": self.drone_mode.value.upper(),
                        "fps": int(self.det_fps()),
                        "logs": list(self._ui_logs)[-30:],
                        "gps_trace": [(p[0], p[1]) for p in list(self._gps_trace)]
                    }
                except Exception as e:
                    return {
                        "altitude": 0.0, "battery": 100, "speed": 0.0,
                        "mode": "MANUAL", "fps": 0,
                        "logs": ["Error: {}".format(str(e))], "gps_trace": []
                    }
            
            return jsonify(self._status_cache.get(compute_status))
        
        # ENHANCED: Nouvelles routes for jauges and controls
        @app.route("/set_rotation_speed", methods=["POST"])
        def set_rotation_speed():
            """Règle vitesse de rotation (ENHANCED)"""
            try:
                data = request.get_json()
                speed_deg_s = float(data.get("speed", 45))
                self.sweep_rate_adjustable = math.radians(speed_deg_s)
                return jsonify({"status": "ok", "speed": speed_deg_s})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 400
        
        @app.route("/set_target_altitude", methods=["POST"])
        def set_target_altitude():
            """Règle altitude cible (ENHANCED)"""
            try:
                data = request.get_json()
                altitude = float(data.get("altitude", 1.5))
                altitude = max(0.5, min(5.0, altitude))
                self.target_alt = altitude
                self.target_altitude = altitude
                return jsonify({"status": "ok", "altitude": altitude})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 400
        
        @app.route("/manual_control", methods=["POST"])
        def manual_control():
            """Control manuel clavier (ENHANCED)"""
            try:
                data = request.get_json()
                key = data.get("key", "").lower()
                action = data.get("action", "press")
                
                if key in self.manual_controls:
                    self.manual_controls[key] = (action == "press")
                    
                    with self._state_lock:
                        # Pitch (before/arrière)
                        if self.manual_controls['z']:
                            self.manual_pitch = 0.1
                        elif self.manual_controls['s']:
                            self.manual_pitch = -0.1
                        else:
                            self.manual_pitch = 0.0
                        
                        # Yaw (rotation)
                        if self.manual_controls['q']:
                            self.manual_yaw = 0.5
                        elif self.manual_controls['d']:
                            self.manual_yaw = -0.5
                        else:
                            self.manual_yaw = 0.0
                        
                        # Altitude
                        if self.manual_controls['e']:
                            self.manual_altitude_delta = 0.01
                        elif self.manual_controls['a']:
                            self.manual_altitude_delta = -0.01
                        else:
                            self.manual_altitude_delta = 0.0
                
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 400
        
        @app.route("/download_logs")
        def download_logs():
            try:
                self.action_logger.finalize()
                return send_file(self.action_logger.log_file, as_attachment=True, download_name=f"drone_log_{self.action_logger.sesifon_id}.json")
            except:
                return jsonify({"error": "No logs"}), 404
        
        # 🆕 ROUTES POUR GESTION DES FILTRES D'ÉVÉNEMENTS
        @app.route("/get_event_filters")
        def get_event_filters():
            """Return current filter state d'événements"""
            try:
                filters = self.action_logger.get_event_filters()
                return jsonify({"status": "ok", "filters": filters})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 400
        
        @app.route("/set_event_filter", methods=["POST"])
        def set_event_filter():
            """Enable/disable an event type in real-time"""
            try:
                data = request.get_json()
                event_type = data.get("event_type")
                enabled = data.get("enabled", True)
                
                if self.action_logger.set_event_filter(event_type, enabled):
                    status_msg = "✅ enabled" if enabled else "❌ désenabled"
                    self._ring(logging.INFO, f"📋 Filter '{event_type}': {status_msg}")
                    return jsonify({"status": "ok", "event_type": event_type, "enabled": enabled})
                else:
                    return jsonify({"status": "error", "message": "Type d'événement invalide"}), 400
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 400

                self._ring(logging.INFO, "🌐 UI: http://localhost:{}/".format(self.HTTP_PORT))
        import logging as pylog
        pylog.getLogger('werkzeug').setLevel(pylog.WARNING)
        app.run(host="0.0.0.0", port=self.HTTP_PORT, debug=False, use_reloader=False, threaded=True)
    
    def run(self):
        """Boucle principale"""
        if not self._ui_started:
            self._ui_thread = threading.Thread(target=self._start_ui, daemon=True)
            self._ui_thread.start()
            self._ui_started = True
            
            # Attendre que Flask démarre
            self._ring(logging.INFO, "⏳ Waiting for web interface to start...")
            time.sleep(2.0)
        
        self._ring(logging.INFO, "✅ Ultimate Drone Controller ready!")
        self._ring(logging.INFO, "📋 Features: Hybrid Tracking | Video Recording | Misifons | RTH | Geofence")
        self._ring(logging.INFO, "🌐 Open browser: http://localhost:{}/".format(self.HTTP_PORT))
        
        while not self._shutdown and self.step(self.time_step) != -1:
            self._control_step()
        
        # Cleanup
        self.action_logger.finalize()
        if self.video_recorder:
            self._cmd_stop_recording()
        
        self._ring(logging.INFO, "✅ Shutdown complete")


if __name__ == "__main__":
    UltimateDroneController().run()
