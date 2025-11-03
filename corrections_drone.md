# 🚁 Corrections pour le problème d'approche du drone

## 📊 Analyse des logs

**Symptômes observés :**
- `bbox_percent` reste constant à **1.66%** (objet très loin)
- `pitch_corr` = **0.10** (correction trop faible)
- `vertical_input` = **-3.0** (drone descend au lieu de maintenir l'altitude)
- `pitch_input` = **0.15** (mouvement avant insuffisant)

---

## 🔧 CORRECTION 1 : Augmenter les gains PID (CRITIQUE)

### Ligne 620 - Avant :
```python
SZ_KP, SZ_KD = 0.0025, 0.00080  # OPTIMISÉ pour approche plus rapide
```

### ✅ Après :
```python
SZ_KP, SZ_KD = 0.015, 0.0050  # GAINS AUGMENTÉS pour approche efficace
# SZ_KP multiplié par 6 (0.0025 → 0.015)
# SZ_KD multiplié par 6 (0.00080 → 0.0050)
```

**Explication :** 
- Avec `bbox_percent = 1.66%`, l'erreur de taille est grande (~30 pixels)
- `pitch_corr` actuel = 0.0025 × 30 = **0.075** (trop faible!)
- `pitch_corr` nouveau = 0.015 × 30 = **0.45** (bien meilleur!)

---

## 🔧 CORRECTION 2 : Ajuster l'altitude cible pendant l'approche

### Ligne 680 - Avant :
```python
self.target_alt = 1.20  # Depuis fichier original
```

### ✅ Après :
```python
self.target_alt = 1.50  # AUGMENTÉ pour éviter descente pendant suivi
```

**ET ajouter dans la logique FOLLOW (après ligne 1170) :**

```python
elif mode == DroneMode.FOLLOW:
    # 🆕 CORRECTION: Maintenir altitude stable pendant le suivi
    if bbox_percent < 15:  # Si objet loin
        self.target_alt = 1.50  # Maintenir altitude élevée
    elif bbox_percent < 25:  # Si objet à distance moyenne
        self.target_alt = 1.35  # Altitude moyenne
    else:  # Si objet proche
        self.target_alt = 1.20  # Altitude basse
    
    # LOG 23-25: Follow mode active avec target info
    self.action_logger.log_event("follow_active", {
        "target_center_x": round(cx, 1),
        "target_center_y": round((y1 + y2) / 2, 1),
        "bbox_width": round(bbox_width, 1),
        "bbox_height": round(bbox_height, 1),
        "bbox_percent": round(bbox_percent, 2)
    })
```

---

## 🔧 CORRECTION 3 : Améliorer la logique des zones d'approche

### Lignes 1188-1224 - Ajustements :

```python
# Zones de distance intelligentes (valeurs ajustées)
ZONE_TOO_CLOSE = 50.0    # >50% = trop proche, reculer (était 40%)
ZONE_OPTIMAL_MAX = 40.0  # 30-40% = distance optimale (était 35%)
ZONE_OPTIMAL_MIN = 30.0  # (était 25%)
ZONE_FAR = 20.0          # <20% = loin, approcher (était 15%)

# LOGIQUE D'APPROCHE INTELLIGENTE
if bbox_percent > ZONE_TOO_CLOSE:
    # TROP PROCHE - Reculer activement
    pitch_corr = -0.20  # Reculer plus fort (était -0.15)
    print(f"[FOLLOW] TROP PROCHE ({bbox_percent:.1f}%) - Recul")

elif bbox_percent > ZONE_OPTIMAL_MAX:
    # PROCHE DE LA LIMITE - Ralentir/Arrêter
    pitch_corr = -0.05  # Recul léger (était -0.03)
    print(f"[FOLLOW] ZONE LIMITE ({bbox_percent:.1f}%) - Maintien")

elif bbox_percent >= ZONE_OPTIMAL_MIN:
    # DISTANCE OPTIMALE - Maintenir position
    pitch_corr = 0.02  # Léger mouvement avant pour compenser drift
    print(f"[FOLLOW] DISTANCE OPTIMALE ({bbox_percent:.1f}%) - Stable")

elif bbox_percent > ZONE_FAR:
    # UN PEU LOIN - Approcher modérément
    base_speed = self.SZ_KP * err_s
    pitch_corr = min(base_speed, 0.40)  # Limité à 0.40 (était 0.25)
    print(f"[FOLLOW] Approche modérée ({bbox_percent:.1f}%)")

else:
    # TRÈS LOIN (<20%) - Approcher rapidement
    pitch_corr = self.SZ_KP * err_s + self.SZ_KD * derr_s
    pitch_corr = clamp(pitch_corr, -0.30, 0.70)  # Limites augmentées!
    print(f"[FOLLOW] Approche rapide ({bbox_percent:.1f}%), pitch_corr={pitch_corr:.3f}")
```

---

## 🔧 CORRECTION 4 : Ajouter un debug amélioré

### Ajouter après ligne 1225 :

```python
# 🆕 DEBUG DÉTAILLÉ pour diagnostiquer l'approche
print(f"[FOLLOW DEBUG] bbox={bbox_percent:.2f}%, err_s={err_s:.1f}, "
      f"pitch_corr={pitch_corr:.3f}, vertical_input={vertical_input:.2f}, "
      f"target_alt={self.target_alt:.2f}, current_alt={z:.2f}")
```

---

## 📋 Résumé des changements

| Paramètre | Avant | Après | Raison |
|-----------|-------|-------|--------|
| `SZ_KP` | 0.0025 | **0.015** | Approche 6× plus rapide |
| `SZ_KD` | 0.00080 | **0.0050** | Stabilisation améliorée |
| `target_alt` initial | 1.20 | **1.50** | Éviter descente |
| Zone TRÈS LOIN | <15% | **<20%** | Déclencher approche plus tôt |
| Limite pitch rapide | 0.50 | **0.70** | Autoriser approche plus agressive |
| Zone optimale | 25-35% | **30-40%** | Zone confort plus large |

---

## 🎯 Résultat attendu

Avec ces corrections :
1. **L'approche sera 6× plus rapide** grâce aux gains augmentés
2. **Le drone maintiendra son altitude** pendant le suivi
3. **L'approche sera plus agressive** quand l'objet est loin (<20%)
4. **La zone de confort est plus large** (30-40% au lieu de 25-35%)

---

## 🚀 Test recommandé

1. Appliquer les corrections
2. Décoller le drone
3. Activer le mode SEARCH
4. Observer les logs console avec le nouveau debug
5. Vérifier que `bbox_percent` augmente progressivement de 1-2% vers 30-40%

---

## 📞 Si le problème persiste

Si après ces corrections l'approche reste lente :
- Augmenter encore `SZ_KP` jusqu'à 0.025
- Vérifier que `pitch_input` dans les logs atteint au moins 0.5 quand l'objet est loin
- S'assurer que `vertical_input` est proche de 0 (±0.5) pour altitude stable
