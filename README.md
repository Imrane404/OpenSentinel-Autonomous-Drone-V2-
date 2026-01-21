# 🚁 Open Sentinel - Webots AI Autonomous Tracking

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Webots](https://img.shields.io/badge/Simulator-Webots%20R2023b+-orange.svg)](https://cyberbotics.com/)
[![YOLO](https://img.shields.io/badge/Inference-YOLOv11-red.svg)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An advanced autonomous UAV control system featuring **real-time Edge-AI visual tracking**. Developed for the **Mavic 2 Pro** platform within the Webots environment, it bridges high-level computer vision with precision flight dynamics.

> 🇬🇧 **English** | 🇫🇷 [Version française](README.fr.md)

![Demo](docs/images/demo.gif)

---

## ⚡ Key Capabilities

### 🎯 Perception & Tracking Pipeline
* **AI Detection Engine:** Leverages **YOLOv11** for real-time identification of COCO classes (humans, vehicles, animals).
* **Hybrid Tracking Fusion:** Combines YOLO detection with **KCF (Kernelized Correlation Filters)** for low-latency persistence between inference frames.
* **Dynamic Response:** 95% reactivity rate ($\alpha=0.95$) with re-detection cycles every 0.3s.
* **Active Framing:** Automatic Yaw centering and Pitch-based distance maintenance (targeting 30-40% of screen occupancy).

### 🎮 Mission Control
* **Web Dashboard:** Modern Flask-based interface with live MJPEG telemetry and command overrides.
* **Autonomous Modes:** * `SEARCH`: 360° situational scanning to locate targets.
    * `FOLLOW`: Active AI-target persistence and centering.
    * `ORBIT`: Constrained circular navigation around targets.
    * `RTH / LAND`: Automated recovery and landing sequences.
* **Safety Stack:** Geofencing, edge-loss detection, and fail-safe motor cut-offs.

---

## 🏗 System Architecture

### Processing Pipeline
```mermaid
graph TD
    A[4K Camera] --> B[YOLOv11 Detector]
    B --> C[KCF Tracker Fusion]
    C --> D[EMA Smoothing Filter]
    D --> E[PID Flight Control]
    E --> F[Mavic 2 Pro Motors]