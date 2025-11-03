# 🚀 Quick Start Guide

Guide d'installation rapide pour démarrer en 5 minutes !

## ⚡ Installation Express

### 1️⃣ Prérequis (2 min)
```bash
# Vérifiez Python
python --version  # Besoin: 3.8+

# Vérifiez Webots
# Télécharger: https://cyberbotics.com/#download
```

### 2️⃣ Installation (2 min)
```bash
# Cloner
git clone https://github.com/votre-username/autonomous-drone-webots.git
cd autonomous-drone-webots

# Installer dépendances
pip install -r requirements.txt
```

### 3️⃣ Lancer (1 min)
```bash
# 1. Ouvrir Webots
# 2. Ouvrir: worlds/mavic_2_pro.wbt
# 3. Cliquer Play ▶️
# 4. Aller sur: http://localhost:5010
```

## 🎮 Premier vol

### Dans le navigateur (http://localhost:5010):

**Étape 1 : Décoller**
```
Cliquez: 🛫 Takeoff
```

**Étape 2 : Chercher un objet**
```
Tapez: "person" (ou "car", "dog", etc.)
Cliquez: 🔍 Start Search
```

**Étape 3 : Regarder la magie opérer ! ✨**
- Le drone tourne et cherche
- Dès détection → Suivi automatique
- L'objet reste centré dans la caméra

**Étape 4 : Atterrir**
```
Cliquez: 🛬 Land
```

## 🎯 Objets détectables

**Populaires:**
- `person` - Personne
- `car` - Voiture
- `bicycle` - Vélo
- `dog` - Chien
- `cat` - Chat
- `bus` - Bus
- `truck` - Camion

**Plus de 80 objets supportés !**
Liste complète: [COCO Dataset](https://tech.amikelive.com/node-718/what-object-categories-labels-are-in-coco-dataset/)

## 🔧 Configuration Rapide

### Changer le port (si 5010 occupé)
```python
# Ligne 644 de drone_controller.py
HTTP_PORT = 5010  # Changer par ex. 5011
```

### Ajuster vitesse de suivi
```python
# Ligne 1204 de drone_controller.py
KP_YAW = 1.2  # Augmenter = rotation plus rapide
```

## 🐛 Problèmes courants

### Erreur: "No module named 'ultralytics'"
```bash
pip install ultralytics opencv-contrib-python
```

### Le drone ne décolle pas
- ✅ Webots en mode "Run" (pas Pause)
- ✅ Temps qui avance dans Webots

### Rien ne se détecte
- ✅ Objet dans le champ de vision (360x240)
- ✅ Distance < 15m
- ✅ Bon nom d'objet (anglais: "person" pas "personne")

### Interface ne charge pas
- ✅ Attendre 3-5 secondes après Play
- ✅ Vérifier console Webots (pas d'erreur Python)
- ✅ Port 5010 libre

## 📚 Aller plus loin

- [README complet](README.md) - Toutes les fonctionnalités
- [Architecture](docs/ARCHITECTURE.md) - Comment ça marche
- [Contribution](CONTRIBUTING.md) - Améliorer le projet

## 💡 Astuces

**Mode Manuel :**
```
Cliquez "Manual Mode"
Z/S : Avant/Arrière
Q/D : Rotation
E/A : Haut/Bas
```

**Enregistrement :**
```
📸 Photo : Capture instantanée
🔴 Rec : Enregistrement vidéo
```

**Logs :**
```
Boutons: ✅ Tout cocher / ❌ Tout décocher
📊 Download Logs : Export JSON
```

---

**Bon vol ! 🚁**

Besoin d'aide ? → [Ouvrir une Issue](https://github.com/votre-username/autonomous-drone-webots/issues)
