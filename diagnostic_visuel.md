# 🎯 DIAGNOSTIC VISUEL - Problème d'approche du drone

## 📊 SITUATION ACTUELLE (AVANT CORRECTION)

```
┌─────────────────────────────────────────────────────────────┐
│  CAMÉRA DRONE (360x240 pixels)                              │
│                                                              │
│                                                              │
│                        🎯 [objet]  ← bbox 59x27 = 1.66%    │
│                           tiny!                              │
│                                                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘

État du drone:
├─ bbox_percent = 1.66% (TRÈS LOIN!)
├─ pitch_corr = 0.10 (TROP FAIBLE)
├─ vertical_input = -3.0 (DESCEND! ❌)
├─ pitch_input = 0.15 (avance trop lentement)
└─ Résultat: Le drone NE S'APPROCHE PAS

Calcul actuel:
err_s = 90 - 59 = 31 pixels
pitch_corr = 0.0025 × 31 = 0.0775 ≈ 0.08
                      ↑
                  GAIN TROP FAIBLE!
```

---

## ✅ SITUATION CORRIGÉE (APRÈS CORRECTIONS)

```
Étape 1: Objet détecté loin
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│                        🎯 [objet]                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
bbox = 1.66% → pitch_corr = 0.45 → APPROCHE RAPIDE! ✅

↓ Le drone avance...

Étape 2: Distance moyenne
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│                    🎯 [objet]                               │
│                      bigger                                  │
└─────────────────────────────────────────────────────────────┘
bbox = 20% → pitch_corr = 0.30 → Approche modérée

↓ Le drone continue...

Étape 3: Distance optimale
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│               🎯 [objet]                                    │
│                  optimal                                     │
└─────────────────────────────────────────────────────────────┘
bbox = 35% → pitch_corr = 0.02 → MAINTIEN ✅
```

---

## 🔍 ANALYSE DÉTAILLÉE DES GAINS PID

### Avant (gains trop faibles):
```
SZ_KP = 0.0025
SZ_KD = 0.00080

Exemple avec objet loin (err_s = 30):
pitch_corr = 0.0025 × 30 + 0.00080 × derr_s
          = 0.075 + dérivée
          ≈ 0.08 - 0.10

Vitesse d'approche: ~0.5 m/s → TROP LENT ❌
Temps pour atteindre distance optimale: 30-40 secondes
```

### Après (gains optimisés):
```
SZ_KP = 0.015  (×6)
SZ_KD = 0.0050 (×6.25)

Exemple avec objet loin (err_s = 30):
pitch_corr = 0.015 × 30 + 0.0050 × derr_s
          = 0.45 + dérivée
          ≈ 0.45 - 0.65

Vitesse d'approche: ~3 m/s → RAPIDE ✅
Temps pour atteindre distance optimale: 5-8 secondes
```

---

## 📈 GRAPHIQUE DES ZONES D'APPROCHE

```
pitch_corr
    ^
0.7 |                    ╱
    |                  ╱
0.5 |                ╱     (APPROCHE RAPIDE)
    |              ╱
0.3 |            ╱         (Approche modérée)
    |          ╱
0.1 |        ╱─────────    (ZONE OPTIMALE: Maintien)
    |                  ╲
0.0 |___________________╲__________________________> bbox_percent
    0   10   20   30   40   50   60
        │    │    │    │    │
       Loin Moyen│ Optimal│ Trop proche
                FAR  ZONE  CLOSE
```

Légende:
- **< 20%** : Approche RAPIDE (pitch_corr jusqu'à 0.70)
- **20-30%** : Approche modérée (pitch_corr ~ 0.30)
- **30-40%** : Zone OPTIMALE (pitch_corr ~ 0.02)
- **40-50%** : Zone limite (pitch_corr négatif, recul léger)
- **> 50%** : TROP PROCHE (pitch_corr négatif, recul fort)

---

## 🎯 FLUX DE CONTRÔLE AMÉLIORÉ

```
┌─────────────────────────────────────┐
│  Détection objet (YOLO + Tracker)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Calcul bbox_percent                 │
│  bbox_area / screen_area × 100      │
└──────────────┬──────────────────────┘
               │
               ▼
       ┌───────────────┐
       │ bbox_percent? │
       └───────┬───────┘
               │
       ┌───────┴────────┬──────────┬───────────┐
       │                │          │           │
       ▼                ▼          ▼           ▼
   < 20%           20-30%      30-40%       > 50%
 TRÈS LOIN          LOIN     OPTIMAL    TROP PROCHE
       │                │          │           │
       ▼                ▼          ▼           ▼
pitch_corr=0.65  pitch_corr=0.30  0.02   pitch_corr=-0.20
       │                │          │           │
       └────────────────┴──────────┴───────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ Ajuster altitude  │
              │ selon distance    │
              └─────────┬─────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ Appliquer moteurs │
              │   pitch_input    │
              │  vertical_input  │
              └──────────────────┘
```

---

## 🧪 TESTS DE VALIDATION

### Test 1: Approche depuis position lointaine
```
Condition initiale:
- Distance: 15 mètres
- bbox_percent: ~2%
- altitude: 1.5m

Résultat attendu:
✅ pitch_corr > 0.45
✅ vertical_input proche de 0
✅ bbox_percent augmente progressivement
✅ Drone atteint zone optimale (30-40%) en 5-8 secondes
```

### Test 2: Maintien en zone optimale
```
Condition initiale:
- Distance: 3-4 mètres
- bbox_percent: ~35%
- altitude: 1.35m

Résultat attendu:
✅ pitch_corr ≈ 0.02 (maintien position)
✅ bbox_percent reste stable (30-40%)
✅ Pas d'oscillations
✅ Altitude maintenue
```

### Test 3: Recul si trop proche
```
Condition initiale:
- Distance: < 2 mètres
- bbox_percent: > 50%
- altitude: 1.2m

Résultat attendu:
✅ pitch_corr < 0 (recul)
✅ bbox_percent diminue vers zone optimale
✅ Drone se repositionne correctement
```

---

## 🐛 CHECKLIST DE DEBUG

Si le problème persiste après corrections:

□ **Vérifier les logs console:**
  - Les messages [FOLLOW] apparaissent-ils?
  - Le mode est-il bien "FOLLOW" et pas "SEARCH"?
  - Les valeurs de pitch_corr sont-elles correctes?

□ **Vérifier les paramètres:**
  - SZ_KP = 0.015 (pas 0.0025)
  - SZ_KD = 0.0050 (pas 0.00080)
  - target_alt = 1.50 (pas 1.20)

□ **Analyser le comportement:**
  - Le drone avance-t-il visiblement?
  - bbox_percent augmente-t-il?
  - vertical_input est-il proche de 0?

□ **Tests additionnels:**
  - Essayer avec SZ_KP = 0.025 (encore plus agressif)
  - Vérifier que l'objet reste dans le champ de vision
  - Tester avec différents objets (person, car, etc.)

---

## 📞 SUPPORT SUPPLÉMENTAIRE

Si après toutes ces corrections le drone ne s'approche toujours pas:

1. **Vérifier la configuration Webots:**
   - Les moteurs répondent-ils correctement?
   - Le GPS et l'IMU sont-ils fonctionnels?

2. **Vérifier la détection:**
   - L'objet est-il bien détecté en continu?
   - Le tracker fonctionne-t-il correctement?

3. **Logs détaillés:**
   - Activer tous les filtres d'événements
   - Télécharger les logs JSON complets
   - Analyser la séquence complète des événements
