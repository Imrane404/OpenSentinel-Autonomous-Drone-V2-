# 📤 Guide de Publication sur GitHub

Guide étape par étape pour publier votre projet.

## 🎯 Prérequis

1. **Compte GitHub** : [Créer un compte](https://github.com/signup)
2. **Git installé** : [Télécharger Git](https://git-scm.com/downloads)
3. **Vérifier Git** :
   ```bash
   git --version
   ```

## 📝 Étape 1 : Préparer les fichiers

### Structure finale de votre projet :
```
autonomous-drone-webots/
├── controllers/
│   └── drone_controller/
│       └── drone_controller.py
├── worlds/
│   └── mavic_2_pro.wbt
├── docs/
│   └── ARCHITECTURE.md
├── README.md
├── QUICKSTART.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

### Copiez les fichiers créés :
```bash
# Copiez tous les fichiers du dossier github_repo vers votre projet
cp README.md votre-projet/
cp requirements.txt votre-projet/
cp .gitignore votre-projet/
cp LICENSE votre-projet/
cp CONTRIBUTING.md votre-projet/
cp QUICKSTART.md votre-projet/
cp CHANGELOG.md votre-projet/
cp -r docs/ votre-projet/
```

## 🚀 Étape 2 : Créer le repository GitHub

### Via le site web :
1. Allez sur [github.com/new](https://github.com/new)
2. **Repository name** : `autonomous-drone-webots`
3. **Description** : "🚁 AI-powered autonomous drone with real-time visual tracking in Webots"
4. **Public** ou **Private** : Votre choix
5. **⚠️ N'INITIALISEZ PAS** avec README/gitignore/license (vous les avez déjà !)
6. Cliquez **Create repository**

## 💻 Étape 3 : Initialiser Git localement

Ouvrez un terminal dans votre dossier projet :

```bash
# 1. Initialiser Git
git init

# 2. Ajouter tous les fichiers
git add .

# 3. Premier commit
git commit -m "feat: initial commit - autonomous drone with visual tracking"

# 4. Renommer branche en 'main'
git branch -M main

# 5. Lier au repository GitHub
# Remplacez VOTRE-USERNAME par votre nom d'utilisateur GitHub
git remote add origin https://github.com/VOTRE-USERNAME/autonomous-drone-webots.git

# 6. Push initial
git push -u origin main
```

### Si vous avez une erreur d'authentification :

**Option A : Token personnel (Recommandé)**
1. Allez sur GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Cochez : `repo`, `workflow`
4. Copiez le token
5. Au push, utilisez :
   - Username : votre-username
   - Password : le token généré

**Option B : GitHub CLI**
```bash
# Installer GitHub CLI: https://cli.github.com/
gh auth login
git push -u origin main
```

## 📸 Étape 4 : Ajouter des images (Optionnel mais recommandé)

### Créer le dossier images :
```bash
mkdir -p docs/images
```

### Captures d'écran à faire :
1. **Interface web** : Capture du dashboard
2. **Tracking en action** : GIF du drone suivant un objet
3. **Modes de vol** : Screenshots différents modes

### Outils pour GIF :
- **Windows** : ScreenToGif
- **Mac** : Kap
- **Linux** : Peek

### Ajouter les images :
```bash
# Copier vos images
cp screenshot.png docs/images/interface.png
cp tracking.gif docs/images/tracking.gif

# Commit
git add docs/images/
git commit -m "docs: add screenshots and demo GIF"
git push
```

## ✨ Étape 5 : Améliorer le README

### Remplacez dans README.md :
```markdown
# Avant
![Demo](docs/images/demo.gif)

# Après (si vous avez créé les images)
![Demo](docs/images/tracking.gif)
```

```markdown
# Avant
git clone https://github.com/votre-username/autonomous-drone-webots.git

# Après
git clone https://github.com/VOTRE-VRAI-USERNAME/autonomous-drone-webots.git
```

```bash
# Commit les changements
git add README.md
git commit -m "docs: update README with correct username and images"
git push
```

## 🏷️ Étape 6 : Ajouter des topics (tags)

Sur GitHub, votre repository → Settings → Topics :

Ajoutez ces topics :
```
python
webots
drone
computer-vision
yolo
autonomous-systems
robotics
ai
opencv
tracking
simulation
flask
```

## 📋 Étape 7 : Créer une Release (Version 1.0.0)

1. Sur GitHub : **Releases** → **Create a new release**
2. **Tag** : `v1.0.0`
3. **Title** : `v1.0.0 - Initial Release 🚁`
4. **Description** :
```markdown
## 🎉 First stable release!

### Features
- Visual tracking with YOLOv11
- Real-time object centering
- Web interface with live video
- 5 flight modes (MANUAL, SEARCH, FOLLOW, ORBIT, RTH)
- Photo/video recording
- Detailed logging system

### Installation
See [Quick Start Guide](QUICKSTART.md)

### Known Issues
- Single object tracking only
- YOLO model auto-download on first run

Full changelog: [CHANGELOG.md](CHANGELOG.md)
```
5. Cliquez **Publish release**

## 🌟 Étape 8 : Promouvoir votre projet

### Ajouter badges au README :
Déjà présents en haut du README :
```markdown
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](...)
[![Webots](https://img.shields.io/badge/Webots-R2023b+-orange.svg)](...)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](...)
```

### Partager sur :
- Reddit : r/robotics, r/Python, r/computervision
- LinkedIn : Post avec GIF démo
- Twitter/X : Thread avec features
- Webots Discord : Showcase channel

### Texte de partage suggéré :
```
🚁 J'ai créé un drone autonome avec suivi visuel IA !

✨ Features :
- YOLOv11 pour détecter 80+ objets
- Suivi en temps réel avec centrage auto
- Interface web avec vidéo live
- 5 modes de vol
- Open-source sur GitHub

Repo : [votre-lien]
Demo : [lien-GIF]

#Python #AI #Robotics #Webots #OpenCV
```

## 🔄 Workflow de développement futur

### Créer une branche pour nouvelle feature :
```bash
git checkout -b feature/multi-object-tracking
# ... développement ...
git add .
git commit -m "feat: add multi-object tracking"
git push origin feature/multi-object-tracking
```

### Créer une Pull Request sur GitHub :
1. GitHub → Compare & pull request
2. Reviewer le code
3. Merge quand prêt

### Mettre à jour main :
```bash
git checkout main
git pull origin main
```

## 📊 Statistiques GitHub

Après quelques jours :
- **Stars** ⭐ : Popularité
- **Forks** 🍴 : Réutilisations
- **Issues** 🐛 : Bugs reportés
- **Pull Requests** 🔀 : Contributions

## ✅ Checklist finale

- [ ] Repository créé sur GitHub
- [ ] Code pushé avec tous les fichiers
- [ ] README personnalisé (username, images)
- [ ] LICENSE ajoutée (MIT)
- [ ] Topics/tags ajoutés
- [ ] Release v1.0.0 créée
- [ ] Screenshots/GIFs ajoutés
- [ ] Projet partagé sur réseaux

## 🎉 Félicitations !

Votre projet est maintenant public et professionnel ! 🚀

### Prochaines étapes :
1. Répondre aux Issues
2. Accepter/reviewer les Pull Requests
3. Maintenir le CHANGELOG
4. Créer de nouvelles releases

---

**Besoin d'aide ?** N'hésitez pas à demander !
