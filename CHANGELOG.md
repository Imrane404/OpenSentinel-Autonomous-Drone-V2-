# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-11-03

### 🎉 Initial Release

#### ✨ Features
- **Visual Tracking System**
  - YOLOv11 object detection
  - Hybrid YOLO + KCF tracking
  - EMA smoothing (alpha=0.95)
  - Real-time object centering with YAW control
  - Distance control with PITCH
  - Dynamic altitude adjustment

- **Flight Modes**
  - MANUAL: Full keyboard control
  - SEARCH: Automatic rotation to find objects
  - FOLLOW: Visual tracking with centering
  - ORBIT: Circle around target
  - RTH: Return to home

- **Web Interface**
  - Real-time MJPEG video stream
  - Modern dashboard with controls
  - Status monitoring
  - Keyboard controls integration

- **Recording & Logging**
  - Photo capture
  - HD video recording
  - Detailed JSON event logging
  - Configurable log filters

- **Safety Features**
  - Geofencing
  - Edge detection
  - Emergency stop
  - PID stabilization

#### 🔧 Technical Specifications
- Python 3.8+ support
- Webots R2023b+ compatible
- 80+ COCO objects detection
- 15-30 FPS detection rate
- ~33ms tracking latency
- ±5% centering precision

#### 📚 Documentation
- Comprehensive README
- Quick Start Guide
- Architecture documentation
- Contributing guidelines
- MIT License

### 🐛 Known Issues
- YOLO model requires manual download on first run
- Limited to single object tracking
- Performance depends on GPU availability

### 🎯 Coming Soon
- [ ] Multi-object tracking
- [ ] Path planning
- [ ] Gesture recognition
- [ ] ROS2 integration

---

## Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

### Types of changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerabilities
