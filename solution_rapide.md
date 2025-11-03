# ⚡ SOLUTION RAPIDE - Problème d'approche drone

## 🔴 Problème
Le drone ne s'approche PAS de l'objet détecté en mode FOLLOW.
- bbox_percent reste à 1.66% (objet très loin)
- pitch_corr = 0.10 (correction trop faible)
- vertical_input = -3.0 (drone descend au lieu de maintenir altitude)

## ✅ Solution en 3 étapes

### 1️⃣ LIGNE 620 - Multiplier les gains PID par 6
```python
# AVANT:
SZ_KP, SZ_KD = 0.0025, 0.00080

# APRÈS:
SZ_KP, SZ_KD = 0.015, 0.0050  # 🔧 CORRIGÉ
```

### 2️⃣ LIGNE 680 - Augmenter altitude initiale
```python
# AVANT:
self.target_alt = 1.20

# APRÈS:
self.target_alt = 1.50  # 🔧 CORRIGÉ
```

### 3️⃣ LIGNES 1188-1191 - Ajuster zones d'approche
```python
# AVANT:
ZONE_TOO_CLOSE = 40.0
ZONE_OPTIMAL_MAX = 35.0
ZONE_OPTIMAL_MIN = 25.0
ZONE_FAR = 15.0

# APRÈS:
ZONE_TOO_CLOSE = 50.0    # 🔧 CORRIGÉ
ZONE_OPTIMAL_MAX = 40.0  # 🔧 CORRIGÉ
ZONE_OPTIMAL_MIN = 30.0  # 🔧 CORRIGÉ
ZONE_FAR = 20.0          # 🔧 CORRIGÉ
```

### 4️⃣ LIGNE 1223 - Augmenter limite pitch pour approche rapide
```python
# AVANT (ligne 1223):
pitch_corr = clamp(pitch_corr, -0.20, 0.50)

# APRÈS:
pitch_corr = clamp(pitch_corr, -0.30, 0.70)  # 🔧 CORRIGÉ
```

---

## 📊 Résultat attendu

| Métrique | Avant | Après |
|----------|-------|-------|
| Vitesse d'approche | ~0.5 m/s | ~3 m/s |
| Temps pour atteindre cible | 30-40 sec | 5-8 sec |
| pitch_corr (objet loin) | 0.08-0.10 | 0.45-0.65 |
| Stabilité altitude | ❌ Descend | ✅ Stable |

---

## 🧪 Test rapide après correction

1. **Redémarrer** la simulation Webots
2. **Décoller** le drone
3. **Activer** mode SEARCH
4. **Observer** la console:
   ```
   [FOLLOW] Approche RAPIDE (1.66%), pitch_corr=0.450
   [FOLLOW] Approche RAPIDE (5.23%), pitch_corr=0.520
   [FOLLOW] Approche modérée (22.45%), pitch_corr=0.310
   [FOLLOW] DISTANCE OPTIMALE (35.2%) - Stable
   ```
5. ✅ **Succès** si bbox_percent atteint 30-40% en moins de 10 secondes

---

## ⚠️ Si ça ne marche toujours pas

Essayez des gains encore plus élevés:
```python
SZ_KP, SZ_KD = 0.025, 0.0080  # Approche TRÈS agressive
```

---

## 📁 Fichiers créés pour vous

1. **corrections_drone.md** - Explication détaillée complète
2. **code_corrige.py** - Tous les snippets de code corrigés
3. **diagnostic_visuel.md** - Diagrammes et analyse visuelle
4. **solution_rapide.md** - Ce fichier (résumé ultra-rapide)

---

## 🎯 Cause racine

Les gains PID `SZ_KP` et `SZ_KD` étaient 6× trop faibles, résultant en:
- pitch_corr = 0.0025 × err_s ≈ 0.08 (insuffisant)
- Le drone "flotte" sur place sans avancer
- L'altitude descend car target_alt trop bas

Avec les corrections, pitch_corr sera 6× plus fort:
- pitch_corr = 0.015 × err_s ≈ 0.45 (efficace!)
- Le drone avance visiblement vers la cible
- L'altitude reste stable

---

**Bon vol! 🚁**
