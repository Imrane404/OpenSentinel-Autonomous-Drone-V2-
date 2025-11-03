# 🚀 Guide Pas-à-Pas : Publier sur GitHub

## ⏱️ Temps estimé : 15 minutes

---

## 📋 ÉTAPE 0 : Préparation (2 min)

### Vérifier que vous avez Git installé

**Windows PowerShell ou CMD :**
```bash
git --version
```

**Résultat attendu :**
```
git version 2.x.x
```

**❌ Si Git n'est pas installé :**
1. Téléchargez : https://git-scm.com/download/win
2. Installez avec les options par défaut
3. Redémarrez votre terminal

---

## 🌐 ÉTAPE 1 : Créer le Repository sur GitHub (3 min)

### 1.1 - Se connecter à GitHub
1. Allez sur https://github.com
2. Connectez-vous (ou créez un compte si nécessaire)

### 1.2 - Créer un nouveau repository
1. Cliquez sur le **"+"** en haut à droite
2. Cliquez sur **"New repository"**

### 1.3 - Remplir les informations

**Repository name :** (choisissez un nom)
```
autonomous-drone-webots
```

**Description :** (optionnel mais recommandé)
```
🚁 AI-powered autonomous drone with real-time visual tracking in Webots
```

**Visibilité :**
- ✅ **Public** (recommandé pour portfolio)
- ⚪ Private (si vous préférez)

**⚠️ IMPORTANT - Ne cochez RIEN d'autre :**
- ❌ **Ne cochez PAS** "Add a README file"
- ❌ **Ne cochez PAS** ".gitignore"
- ❌ **Ne cochez PAS** "Choose a license"

*(Vous avez déjà ces fichiers !)*

### 1.4 - Créer le repository
Cliquez sur **"Create repository"**

### 1.5 - Copier l'URL
Vous verrez une page avec des instructions. **Copiez l'URL** qui ressemble à :
```
https://github.com/VOTRE-USERNAME/autonomous-drone-webots.git
```

---

## 💻 ÉTAPE 2 : Préparer les Fichiers (2 min)

### 2.1 - Aller dans votre dossier projet

**PowerShell :**
```powershell
cd C:\Users\surre\Documents\Test_Drone\Autonomous_Drone
```

### 2.2 - Vérifier que vous êtes au bon endroit
```bash
dir
```

**Vous devriez voir :**
- 📁 `controllers/`
- 📁 `worlds/`
- 📄 `README.md` (si vous l'avez copié)

### 2.3 - Copier tous les fichiers du package GitHub

**Ouvrez l'Explorateur Windows :**
1. Allez dans le dossier téléchargé : `github_package/`
2. **Copiez tous les fichiers** vers votre dossier projet :

Fichiers à copier :
```
✅ README.md
✅ README.fr.md
✅ LICENSE
✅ requirements.txt
✅ .gitignore
✅ CONTRIBUTING.md
✅ QUICKSTART.md
✅ CHANGELOG.md
✅ docs/ARCHITECTURE.md
✅ controllers/drone_controller/drone_controller.py (version anglaise)
```

**⚠️ IMPORTANT :** Remplacez le `drone_controller.py` par la version anglaise !

### 2.4 - Personnaliser les fichiers

**Ouvrez README.md avec Notepad :**
```
Chercher/Remplacer :
  - Chercher : votre-username
  - Remplacer par : VOTRE-VRAI-USERNAME-GITHUB
```

**Ouvrez LICENSE avec Notepad :**
```
Ligne 3 : Remplacer [Votre Nom] par votre vrai nom
```

---

## 🔧 ÉTAPE 3 : Initialiser Git (2 min)

### 3.1 - Ouvrir PowerShell dans votre dossier

**Option A - Via Explorateur Windows :**
1. Ouvrez le dossier du projet dans l'Explorateur
2. Dans la barre d'adresse, tapez : `powershell`
3. Appuyez sur Entrée

**Option B - Via commande :**
```powershell
cd C:\Users\surre\Documents\Test_Drone\Autonomous_Drone
powershell
```

### 3.2 - Initialiser Git
```bash
git init
```

**Résultat attendu :**
```
Initialized empty Git repository in C:/Users/surre/.../Autonomous_Drone/.git/
```

### 3.3 - Configurer votre identité (première fois seulement)

**Remplacez par VOS vraies informations :**
```bash
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@example.com"
```

**Exemple :**
```bash
git config --global user.name "Jean Dupont"
git config --global user.email "jean.dupont@gmail.com"
```

---

## 📦 ÉTAPE 4 : Ajouter les Fichiers (2 min)

### 4.1 - Vérifier les fichiers à ajouter
```bash
git status
```

**Vous verrez une liste de fichiers en rouge** (non trackés)

### 4.2 - Ajouter tous les fichiers
```bash
git add .
```

*(Le point signifie "tout")*

### 4.3 - Vérifier que c'est bon
```bash
git status
```

**Maintenant les fichiers sont en vert** (prêts à être commités)

---

## 💾 ÉTAPE 5 : Premier Commit (1 min)

### 5.1 - Créer le commit
```bash
git commit -m "feat: initial commit - autonomous drone with visual tracking"
```

**Résultat attendu :**
```
[main (root-commit) abc1234] feat: initial commit - autonomous drone with visual tracking
 XX files changed, XXXX insertions(+)
 create mode 100644 README.md
 ...
```

### 5.2 - Renommer la branche en "main"
```bash
git branch -M main
```

---

## 🚀 ÉTAPE 6 : Pousser sur GitHub (3 min)

### 6.1 - Lier au repository GitHub

**Remplacez VOTRE-USERNAME par votre vrai username :**
```bash
git remote add origin https://github.com/VOTRE-USERNAME/autonomous-drone-webots.git
```

**Exemple :**
```bash
git remote add origin https://github.com/jdupont/autonomous-drone-webots.git
```

### 6.2 - Vérifier que c'est lié
```bash
git remote -v
```

**Résultat attendu :**
```
origin  https://github.com/VOTRE-USERNAME/autonomous-drone-webots.git (fetch)
origin  https://github.com/VOTRE-USERNAME/autonomous-drone-webots.git (push)
```

### 6.3 - Pousser les fichiers
```bash
git push -u origin main
```

**⚠️ Authentification GitHub :**

Vous allez voir :
```
Username for 'https://github.com':
```

**Entrez votre username GitHub**

```
Password for 'https://VOTRE-USERNAME@github.com':
```

**⚠️ NE PAS ENTRER VOTRE MOT DE PASSE !**

**À la place, utilisez un Personal Access Token :**

#### Comment créer un Token :
1. Allez sur : https://github.com/settings/tokens
2. Cliquez **"Generate new token"** → **"Generate new token (classic)"**
3. Note : `Webots Drone Project`
4. Cochez : ✅ **repo** (tout)
5. Cliquez **"Generate token"** en bas
6. **COPIEZ LE TOKEN** (vous ne le reverrez plus !)
7. **Collez-le** comme "password" dans le terminal

**Le push commence :**
```
Enumerating objects: 50, done.
Counting objects: 100% (50/50), done.
Compressing objects: 100% (45/45), done.
Writing objects: 100% (50/50), 150 KB | 5 MB/s, done.
Total 50 (delta 5), reused 0 (delta 0)
To https://github.com/VOTRE-USERNAME/autonomous-drone-webots.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

✅ **SUCCÈS !**

---

## 🎉 ÉTAPE 7 : Vérifier sur GitHub (1 min)

### 7.1 - Ouvrir votre repository
```
https://github.com/VOTRE-USERNAME/autonomous-drone-webots
```

### 7.2 - Vérifier que tout est là
Vous devriez voir :
- ✅ README.md affiché
- ✅ Badges en haut (Python, Webots, etc.)
- ✅ Dossiers `controllers/`, `worlds/`, `docs/`
- ✅ Tous les fichiers

### 7.3 - Tester les liens
- Cliquez sur `QUICKSTART.md`
- Cliquez sur `CONTRIBUTING.md`
- Vérifiez que tout s'affiche bien

---

## ⭐ ÉTAPE 8 : Améliorer le Repository (optionnel, 5 min)

### 8.1 - Ajouter des Topics (tags)

Sur GitHub, en haut de votre repository :
1. Cliquez sur **⚙️ (Settings)** → ou l'icône d'engrenage à côté de "About"
2. Ajoutez des topics :
```
python webots drone computer-vision yolo autonomous-systems
robotics ai opencv tracking simulation flask
```
3. Cliquez **"Save changes"**

### 8.2 - Créer une Release

1. Cliquez sur **"Releases"** (à droite)
2. Cliquez **"Create a new release"**
3. Tag : `v1.0.0`
4. Title : `v1.0.0 - Initial Release 🚁`
5. Description :
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

Full changelog: [CHANGELOG.md](CHANGELOG.md)
```
6. Cliquez **"Publish release"**

### 8.3 - Activer GitHub Pages (pour la doc - optionnel)

1. Settings → Pages
2. Source : **Deploy from a branch**
3. Branch : **main** → Folder : **/docs**
4. Save

---

## 📝 ÉTAPE 9 : Commandes pour le Futur

### Après avoir modifié des fichiers :

```bash
# 1. Voir ce qui a changé
git status

# 2. Ajouter les fichiers modifiés
git add .

# 3. Créer un commit
git commit -m "fix: correction de [ce que vous avez corrigé]"

# 4. Pousser sur GitHub
git push
```

### Types de messages de commit :
```
feat: nouvelle fonctionnalité
fix: correction de bug
docs: documentation
refactor: refactoring code
perf: amélioration performance
test: tests
chore: maintenance
```

---

## 🐛 Dépannage

### Erreur : "git: command not found"
**Solution :** Installez Git depuis https://git-scm.com/download/win

### Erreur : "remote origin already exists"
**Solution :**
```bash
git remote remove origin
git remote add origin https://github.com/VOTRE-USERNAME/autonomous-drone-webots.git
```

### Erreur : "Authentication failed"
**Solution :** Utilisez un Personal Access Token au lieu du mot de passe
- Guide : https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

### Erreur : "Updates were rejected"
**Solution :**
```bash
git pull origin main --rebase
git push origin main
```

### Le README ne s'affiche pas bien
**Solution :** 
- Vérifiez les liens relatifs
- Vérifiez que le fichier s'appelle exactement `README.md`

---

## ✅ Checklist Finale

Avant de partager votre projet, vérifiez :

- [ ] README.md personnalisé (votre username)
- [ ] LICENSE personnalisée (votre nom)
- [ ] Tous les fichiers poussés sur GitHub
- [ ] README s'affiche correctement
- [ ] Topics/tags ajoutés
- [ ] Release v1.0.0 créée
- [ ] Liens fonctionnels
- [ ] Screenshots ajoutés (optionnel)

---

## 🎯 Prochaines Étapes

### Partager votre projet :
1. **LinkedIn** : Post avec screenshot
2. **Twitter/X** : Thread avec démo
3. **Reddit** : r/robotics, r/Python, r/computervision
4. **Discord Webots** : Showcase channel

### Templates de partage disponibles :
Voir : `SOCIAL_MEDIA_TEMPLATES.md`

---

## 🎉 Félicitations !

Votre projet est maintenant **live sur GitHub** ! 🚀

**URL de votre projet :**
```
https://github.com/VOTRE-USERNAME/autonomous-drone-webots
```

Partagez-le avec le monde ! 🌍

---

**Besoin d'aide ?**
- Documentation Git : https://git-scm.com/doc
- GitHub Help : https://docs.github.com
- Ou ouvrez une Issue sur votre repo !

**Bon succès ! 🍀**
