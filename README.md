# 🚁 Open Sentinel - Webots AI Tracking

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Webots](https://img.shields.io/badge/Webots-R2023b+-orange.svg)](https://cyberbotics.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![YOLO](https://img.shields.io/badge/YOLO-v11-red.svg)](https://github.com/ultralytics/ultralytics)

> 🇬🇧 English

An advanced autonomous drone controller with **real-time AI-powered visual tracking**, developed for the Webots simulator and Mavic 2 Pro drone.

![Demo](docs/images/demo.gif)

## ✨ Features

### 🎯 Intelligent Visual Tracking
- **AI Detection**: YOLOv11 to detect any object (person, car, animal, etc.)
- **Hybrid Tracking**: YOLO + KCF fusion for smooth and robust tracking
- **Automatic Centering**: Drone rotates to keep object centered in camera
- **Distance Control**: Automatically maintains optimal distance (30-40% of screen)
- **Real-time Tracking**: 95% reactivity (alpha=0.95) with re-detection every 0.3s

### 🎮 Advanced Control
- **Complete Web Interface**: Modern dashboard with live video feed
- **Multiple Flight Modes**:
  - 🔍 **SEARCH**: Automatic rotation to find objects
  - 🎯 **FOLLOW**: Active visual tracking with centering
  - 🔄 **ORBIT**: Circle around target
  - 🏠 **RTH**: Automatic return to home
  - ✋ **MANUAL**: Full keyboard control
- **Keyboard Controls**: WASD + keys for altitude/rotation
- **Live Adjustments**: Adjustable altitude and rotation speed

### 📹 Recording & Logs
- **Photo/Video Capture**: HD recording with annotations
- **Detailed JSON Logs**: All events with timestamps
- **Customizable Filters**: Enable/disable log types in real-time
- **Log Download**: JSON export for analysis

### 🛡️ Safety & Stabilization
- **Geofencing**: Configurable safety zone
- **Edge Detection**: Automatic stop if object near image edge
- **Optimized PID Control**: Roll/pitch/yaw stabilization
- **Dynamic Altitude Adjustment**: Altitude adapted to object distance

## 🎬 Demo

### Web Interface
![Interface](docs/images/interface.png)

### Tracking in Action
![Tracking](docs/images/tracking.gif)

### Console Output
```
[FOLLOW] YAW recentering: err_x=-45px (-12.5%), yaw_corr=+0.167
[FOLLOW DEBUG] bbox=18.2% | err_x=-45px(-12.5%) | yaw=+0.167 | pitch=-0.420
[FOLLOW] ✅ OPTIMAL ZONE (35.4%) - Centered=2.1%
```

## 📋 Prerequisites

- **Webots R2023b+**: [Download](https://cyberbotics.com/#download)
- **Python 3.8+**
- **4GB RAM minimum** (8GB recommended for YOLO)
- **GPU optional** (to accelerate YOLO)

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/Imrane404/OpenSentinel-Autonomous-Drone-V2-.git
cd OpenSentinel-Autonomous-Drone-V2-
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Download YOLO model (optional)
```bash
# Model will be automatically downloaded on first launch
# Or manually download yolo11n.pt to the controller folder
```

### 4. Open Webots world
```bash
# Open Webots
# File > Open World > mavic_2_pro.wbt
```

### 5. Start simulation
- Click ▶️ Play in Webots
- Open http://localhost:5010 in your browser

## 🎮 Usage

### Web Interface (http://localhost:5010)

#### 1️⃣ Takeoff
- Click **🛫 Takeoff**
- Drone rises to 1.5m

#### 2️⃣ Search for Object
- Enter object name: `person`, `car`, `dog`, etc.
- Click **🔍 Start Search**
- Drone rotates to search

#### 3️⃣ Automatic Tracking
- Once object detected → Automatic switch to **FOLLOW** mode
- Drone:
  - **Rotates** to center object horizontally
  - **Moves forward/backward** to maintain optimal distance
  - **Adjusts altitude** based on distance

#### 4️⃣ Manual Control
- Click **Manual Mode**
- Use keyboard:
  - `W` / `S`: Forward / Backward
  - `A` / `D`: Rotate left / right
  - `E` / `C`: Up / Down

#### 5️⃣ Return and Landing
- **🏠 RTH**: Automatic return to start point
- **🛬 Land**: Immediate landing
- **🚨 Emergency**: Emergency stop

### Keyboard Controls (Manual Mode)
```
W : Forward
S : Backward
A : Rotate left
D : Rotate right
E : Up
C : Down
```

## ⚙️ Configuration

### Tracking Parameters (lines 620-635 of `drone_controller.py`)
```python
# PID gains for approach
SZ_KP = 0.015   # Approach speed
SZ_KD = 0.0050  # Stabilization

# YAW control for centering
KP_YAW = 1.2    # Rotation speed (line 1204)
YAW_DEADZONE = 0.05  # Centering tolerance (5%)

# Distance zones
ZONE_OPTIMAL_MIN = 30.0  # 30-40% of screen
ZONE_OPTIMAL_MAX = 40.0
```

### Tracker Parameters (lines 249-255)
```python
redetect_interval = 0.3   # YOLO re-detection (seconds)
alpha = 0.95              # Smoothing reactivity (0-1)
max_failures = 15         # Tracking loss tolerance
```

### HTTP Port (line 644)
```python
HTTP_PORT = 5010  # Change if port is occupied
```

## 📁 Project Structure

```
autonomous-drone-webots/
├── controllers/
│   └── drone_controller/
│       ├── drone_controller.py      # Main controller
│       ├── yolo11n.pt              # YOLO model (auto-downloaded)
│       └── drone_flight_log.json   # Flight logs
├── worlds/
│   └── mavic_2_pro.wbt             # Webots world
├── docs/
│   ├── images/                      # Screenshots and GIFs
│   └── ARCHITECTURE.md              # Architecture documentation
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── README.fr.md                     # French version
├── LICENSE                          # MIT License
└── .gitignore                       # Files to ignore
```

## 🏗️ Architecture

### Processing Pipeline
```
┌─────────────┐
│   Camera    │ 360x240 @ 30 FPS
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ YOLO Detect │ Every 0.3s
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ KCF Tracker │ Between detections
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ EMA Filter  │ Smoothing (alpha=0.95)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  PID Yaw    │ Horizontal centering
│  PID Pitch  │ Distance control
│  PID Roll   │ Stabilization
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Motors    │ 4 propellers
└─────────────┘
```

### Key Components

#### 1. HybridTracker (lines 235-474)
- YOLO (detection) + KCF (fast tracking) fusion
- Asynchronous thread for YOLO
- EMA smoothing for stability

#### 2. Visual Control (lines 1176-1300)
- **YAW**: Rotation to center horizontally
- **PITCH**: Forward/backward for optimal distance
- **Altitude**: Dynamic adjustment based on distance

#### 3. Flask Interface (lines 1510-2660)
- Real-time MJPEG streaming
- REST API for commands
- Modern HTML5 dashboard

## 🔧 Troubleshooting

### Drone doesn't take off
- Check that Webots is in "Run" mode
- Simulation must be running (time advancing)

### YOLO detects nothing
- Supported objects: person, car, dog, cat, bicycle, motorcycle, etc.
- See full list: [COCO classes](https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/datasets/coco.yaml)
- Max distance: ~15m

### Tracking is unstable
- Increase `alpha` (line 1081) → More reactive but jittery
- Decrease `KP_YAW` (line 1204) → Smoother rotation

### Port 5010 already in use
- Modify `HTTP_PORT` line 644
- Restart simulation

### Error "No module named 'ultralytics'"
```bash
pip install ultralytics opencv-contrib-python
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| Detection FPS | 15-30 FPS |
| Tracking latency | ~33ms |
| Centering precision | ±5% |
| Approach time (15m) | 5-8 seconds |
| Optimal zone | 30-40% screen |
| CPU usage | 40-60% (without GPU) |
| RAM usage | 2-4 GB |

## 🛣️ Roadmap

- [x] Visual tracking with automatic centering
- [x] Complete web interface
- [x] Multiple flight modes
- [x] Video recording
- [x] Detailed logs
- [ ] Multi-object tracking
- [ ] Path planning with obstacles
- [ ] Gesture recognition
- [x] ROS2 integration (currently available on the IRL Project, Using Mavic Air2 S and ROS-2 Kilted Kaiju)
- [x] Real drone support (PX4/ArduPilot, currently available on the IRL Project, Using LiDAR Sensors)

## 🤝 Contributing

Contributions are welcome! Feel free to:
1. Fork the project
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- **Webots**: Open-source robotics simulator
- **Ultralytics YOLO**: Object detection model
- **OpenCV**: Computer vision library
- **Flask**: Python web framework

## 📧 Contact

For questions or suggestions:
- Open an [Issue](https://github.com/Imrane404/autonomous-drone-webots/issues)
- Pull Requests welcome!

---

⭐ If this project was helpful, don't forget to give it a star!

🇫🇷 [Version française disponible](README.fr.md)
