# 🏗️ Architecture du Système

Documentation technique détaillée du contrôleur de drone autonome.

## 📊 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    DRONE CONTROLLER                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Sensors    │  │   AI Engine  │  │  Web Server  │     │
│  │              │  │              │  │              │     │
│  │ - Camera     │→ │ - YOLO       │→ │ - Flask      │     │
│  │ - GPS        │  │ - KCF        │  │ - MJPEG      │     │
│  │ - IMU        │  │ - EMA Filter │  │ - WebSocket  │     │
│  │ - Gyro       │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                           ▼                                 │
│                  ┌──────────────┐                          │
│                  │ PID Control  │                          │
│                  │ - Yaw        │                          │
│                  │ - Pitch      │                          │
│                  │ - Roll       │                          │
│                  │ - Altitude   │                          │
│                  └──────┬───────┘                          │
│                         │                                   │
│                         ▼                                   │
│                  ┌──────────────┐                          │
│                  │    Motors    │                          │
│                  │  4 Propellers │                          │
│                  └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Pipeline de détection et suivi

### Étape 1 : Acquisition image
```python
Camera (360x240 @ 30 FPS)
    │
    ▼
get_camera_bgr()  # Conversion BGR
    │
    ▼
Frame disponible pour traitement
```

### Étape 2 : Détection AI (Thread asynchrone)
```python
HybridTracker.update(frame)
    │
    ├─→ YOLO Detection (toutes les 0.3s)
    │   │
    │   ├─→ yolo(frame, conf=0.25)
    │   ├─→ Filtre par classe
    │   └─→ Sélection meilleure bbox
    │
    ├─→ KCF Tracking (entre détections)
    │   │
    │   ├─→ tracker.update(frame)
    │   └─→ Prédiction position
    │
    └─→ Fusion résultats
        │
        ├─→ Si YOLO: Réinit KCF
        ├─→ Si KCF: Utilise prédiction
        └─→ EMA smoothing (alpha=0.95)
```

### Étape 3 : Contrôle visuel
```python
Bbox détectée
    │
    ├─→ Calcul erreurs
    │   │
    │   ├─→ err_x = centre_écran - centre_objet
    │   ├─→ err_y = vertical
    │   └─→ err_size = taille_optimale - taille_actuelle
    │
    ├─→ Contrôle YAW (centrage horizontal)
    │   │
    │   ├─→ Zone morte ±5%
    │   ├─→ PID: yaw_corr = KP * err_x + KD * derr_x
    │   └─→ Limite: ±0.5
    │
    ├─→ Contrôle PITCH (distance)
    │   │
    │   ├─→ Zones: 20%, 30-40%, 50%
    │   ├─→ PID: pitch_corr = KP * err_size + KD * derr_size
    │   └─→ Limite: -0.70 à +0.30
    │
    └─→ Contrôle ALTITUDE
        │
        ├─→ Si loin (>15%): 1.50m
        ├─→ Si moyen: 1.35m
        └─→ Si proche (<25%): 1.20m
```

### Étape 4 : Application commandes moteurs
```python
PID Roll/Pitch/Yaw
    │
    ├─→ Roll stabilisation
    ├─→ Pitch mouvement
    ├─→ Yaw rotation
    └─→ Altitude contrôle
        │
        ▼
Calcul vitesses moteurs
    │
    ├─→ FL = K_VERTICAL + vertical - roll + pitch - yaw
    ├─→ FR = -(K_VERTICAL + vertical + roll + pitch + yaw)
    ├─→ RL = -(K_VERTICAL + vertical - roll - pitch + yaw)
    └─→ RR = K_VERTICAL + vertical + roll - pitch - yaw
        │
        ▼
Moteurs (60-80 rad/s)
```

## 🧩 Composants principaux

### 1. DroneActionLogger
**Rôle :** Logging structuré des événements

**Features :**
- Filtres par type d'événement
- Export JSON horodaté
- Buffer en mémoire
- Flush périodique

**Code (lignes 56-161):**
```python
logger.log_event("follow_active", {
    "bbox_percent": 35.2,
    "err_x": -45,
    "yaw_corr": 0.167
})
```

### 2. HybridTracker
**Rôle :** Fusion YOLO + KCF pour suivi robuste

**Architecture :**
```python
class HybridTracker:
    # Détection
    yolo: YOLO          # Modèle de détection
    target_class: str   # Classe recherchée
    
    # Tracking
    tracker: KCF        # Tracker OpenCV
    tracking_active: bool
    
    # Lissage
    bbox_ema: tuple     # Bbox lissée
    detection_history: list  # Historique
    
    # Threading
    detection_thread: Thread
    detection_queue: Queue
```

**Avantages :**
- ✅ Détection précise (YOLO)
- ✅ Tracking rapide (KCF)
- ✅ Robuste aux occultations
- ✅ Pas de freeze (threading)

### 3. Mode FOLLOW (Suivi visuel)
**Rôle :** Garde l'objet centré et à distance optimale

**Contrôleurs :**

#### Yaw (Rotation horizontale)
```python
# Objectif: err_x = 0
KP_YAW = 1.2
KD_YAW = 0.3
YAW_DEADZONE = 5%

yaw_corr = KP * err_x_norm + KD * derr_x
Limite: ±0.5 rad/s
```

#### Pitch (Avant/Arrière)
```python
# Objectif: bbox = 30-40% écran
SZ_KP = 0.015
SZ_KD = 0.0050

Zones:
- >50%: Trop proche → Recul (+0.20)
- 40-50%: Limite → Ralenti (+0.05)
- 30-40%: ✅ Optimal → Maintien (0.0)
- 20-30%: Loin → Approche (-0.40)
- <20%: Très loin → Approche rapide (-0.70)
```

#### Altitude (Vertical)
```python
# Ajustement dynamique
if bbox_percent < 15:
    target_alt = 1.50m  # Vue large
elif bbox_percent < 25:
    target_alt = 1.35m  # Vue moyenne
else:
    target_alt = 1.20m  # Vue rapprochée
```

### 4. Interface Web Flask
**Rôle :** Dashboard temps réel

**Routes :**
- `GET /` - Interface HTML
- `GET /video_feed` - Stream MJPEG
- `POST /action` - Commandes drone
- `POST /search` - Démarrer recherche
- `GET /status` - État drone (JSON)
- `POST /manual_control` - Contrôle clavier

**Streaming vidéo :**
```python
def gen_mjpeg():
    while True:
        frame = get_camera_bgr()
        frame = annotate(frame, bbox)
        _, buffer = cv2.imencode('.jpg', frame)
        yield b'--frame\r\n' + buffer.tobytes()
```

## 🔢 Paramètres critiques

### Détection
| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `redetect_interval` | 0.3s | Fréquence YOLO |
| `alpha` | 0.95 | Réactivité lissage |
| `max_failures` | 15 | Tolérance perte |
| `min_bbox_size` | 15px | Taille min détection |

### Contrôle
| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `KP_YAW` | 1.2 | Gain rotation |
| `YAW_DEADZONE` | 5% | Zone morte centrage |
| `SZ_KP` | 0.015 | Gain distance |
| `K_VERTICAL_P` | 3.0 | Gain altitude |

### Zones
| Zone | Seuil | Action |
|------|-------|--------|
| Trop proche | >50% | Recul |
| Limite | 40-50% | Ralenti |
| ✅ Optimal | 30-40% | Maintien |
| Loin | 20-30% | Approche |
| Très loin | <20% | Approche rapide |

## 🎛️ Modes de vol

### MANUAL
- Contrôle clavier direct
- Stabilisation PID seule
- Pas de tracking

### SEARCH
- Rotation automatique (45°/s)
- Détection YOLO active
- Auto-switch vers FOLLOW

### FOLLOW
- **Suivi visuel actif** ✨
- YAW: Centrage horizontal
- PITCH: Contrôle distance
- Altitude dynamique

### ORBIT
- Rotation constante (0.2 rad/s)
- Maintien distance
- Centrage horizontal

### RTH (Return To Home)
- Navigation GPS vers home
- Atterrissage automatique à <0.5m
- Sécurité geofence

## 📈 Optimisations

### Performance
1. **Threading YOLO** → Pas de freeze (33ms → 0ms perceived)
2. **KCF entre détections** → 60 FPS tracking
3. **EMA smoothing** → Bbox stable
4. **Cache status** → API rapide (100ms → 10ms)

### Stabilité
1. **Zone morte YAW** → Pas d'oscillations
2. **PID dérivé** → Amortissement
3. **Limites strictes** → Sécurité
4. **Detection history** → Robustesse

### Réactivité
1. **alpha = 0.95** → 95% nouvelles données
2. **redetect = 0.3s** → 3 FPS YOLO
3. **KCF = 30 FPS** → Suivi fluide
4. **PID optimisé** → Réponse rapide

## 🔧 Debugging

### Logs console
```
[FOLLOW] Recentrage YAW: err_x=-45px (-12.5%), yaw_corr=+0.167
[FOLLOW DEBUG] bbox=18.2% | err_x=-45px | yaw=+0.167 | pitch=-0.420
[FOLLOW] ✅ ZONE OPTIMALE (35.4%) - Centré=2.1%
```

### Logs JSON
```json
{
  "event_type": "follow_active",
  "elapsed_time": 35.147,
  "data": {
    "target_center_x": 180.5,
    "bbox_percent": 35.2,
    "yaw_corr": 0.167
  }
}
```

### Filtres activables
- ✅ `follow_active` - État suivi
- ✅ `control_commands` - Commandes moteurs
- ⚠️ `altitude_control` - (Haute fréquence)
- ⚠️ `imu_data` - (Très haute fréquence)

## 🚀 Évolutions possibles

### Court terme
- [ ] PID auto-tuning
- [ ] Multi-objets tracking
- [ ] Gestures recognition

### Moyen terme
- [ ] Path planning avec A*
- [ ] Obstacle avoidance
- [ ] Formation flight (multi-drones)

### Long terme
- [ ] Deep RL pour contrôle
- [ ] SLAM visuel
- [ ] Intégration ROS2
- [ ] Support drone réel

---

**Questions ?** → [Ouvrir une Issue](https://github.com/votre-username/autonomous-drone-webots/issues)
