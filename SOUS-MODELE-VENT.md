# Sous-modèles vent et rafales

Station GRENOBLE-CEA-RADOME : vent moyen à 10 m (m/s) et rafale maximale de l'heure (m/s). Test honnête : chaque mois de 2025-10-01 à 2026-10-08 est prédit par un modèle entraîné sans ce mois (entraînement depuis 2024-02-01). Toutes les prévisions sont notées sur les mêmes heures.

Sous-modèle : gradient boosting (scikit-learn) sur tous les paramètres de tous les modèles, l'heure, la saison et les observations connues au moment de la prévision. « Corrigé » : chaque modèle seul recalé par une droite a·prévision + b apprise sur les mois d'entraînement. Heure venteuse = rafale ≥ 10 m/s ; « vues » = part des heures venteuses annoncées, « fausses alertes » = part des heures annoncées venteuses qui ne l'étaient pas.

## Résumé (erreur moyenne en m/s)

| Paramètre | Échelle | Sous-modèle | Meilleur modèle seul | Meilleur modèle corrigé | Moyenne simple |
|---|---|---|---|---|---|
| Vent moyen | Veille → lendemain, heure par heure | **0.59** | 0.86 (icon_eu) | 0.74 (meteoswiss_icon_ch2) | 0.84 |
| Rafales | Veille → lendemain, heure par heure | **1.47** | 2.10 (icon_d2) | 1.77 (meteoswiss_icon_ch2) | 2.04 |
| Vent moyen | Tendance (modèles globaux), J+1 | **0.59** | 0.86 (icon_eu) | 0.74 (meteoswiss_icon_seamless) | 0.77 |
| Rafales | Tendance (modèles globaux), J+1 | **1.47** | 2.10 (icon_seamless) | 1.77 (meteoswiss_icon_seamless) | 2.29 |
| Vent moyen | Tendance (modèles globaux), J+3 | **0.66** | 0.90 (icon_seamless) | 0.76 (meteoswiss_icon_seamless) | 0.80 |
| Rafales | Tendance (modèles globaux), J+3 | **1.68** | 2.35 (icon_seamless) | 1.88 (meteoswiss_icon_seamless) | 2.47 |
| Vent moyen | Tendance (modèles globaux), J+5 | **0.74** | 0.97 (icon_seamless) | 0.83 (ecmwf_aifs025_single) | 0.90 |
| Rafales | Tendance (modèles globaux), J+5 | **1.89** | 3.54 (icon_seamless) | 2.19 (gem_seamless) | 2.57 |
| Vent moyen | Tendance (modèles globaux), J+7 | **0.78** | 1.03 (gfs_seamless) | 0.84 (ecmwf_aifs025_single) | 0.95 |
| Rafales | Tendance (modèles globaux), J+7 | **2.04** | 3.86 (gem_seamless) | 2.27 (gem_seamless) | 3.77 |

## Détection des heures venteuses (rafale ≥ 10 m/s)

| Échelle | Heures venteuses | Sous-modèle : vues / fausses alertes | Meilleur modèle seul : vues / fausses alertes |
|---|---|---|---|
| Veille → lendemain, heure par heure | 776 | 51 % / 29 % | 67 % / 49 % (icon_d2) |
| Tendance (modèles globaux), J+1 | 776 | 52 % / 29 % | 67 % / 49 % (icon_seamless) |
| Tendance (modèles globaux), J+3 | 758 | 37 % / 33 % | 26 % / 44 % (icon_seamless) |
| Tendance (modèles globaux), J+5 | 780 | 25 % / 43 % | 67 % / 77 % (icon_seamless) |
| Tendance (modèles globaux), J+7 | 825 | 10 % / 42 % | 2 % / 68 % (gem_seamless) |

## Conclusions

- Le sous-modèle a la plus petite erreur partout : vent moyen 0,59 m/s la veille contre 0,86 pour le meilleur modèle seul (ICON-EU) et 0,74 pour le meilleur modèle corrigé ; rafales 1,47 m/s contre 2,10 et 1,77.
- L'écart reste net jusqu'à J+7 (vent 0,78 contre 0,84 corrigé ; rafales 2,04 contre 2,27).
- Les modèles bruts ont de gros biais (GFS et GEM sous-estiment les rafales de 3,5 m/s, ICON-CH et HARMONIE surestiment le vent) ; une simple droite par modèle ramène l'erreur des rafales la veille de 2,1-3,8 à 1,8-2,4 m/s.
- Heures venteuses la veille : le sous-modèle en voit 51 % avec 29 % de fausses alertes ; ICON-D2 brut en voit 67 % mais avec 49 % de fausses alertes. Le sous-modèle vise l'erreur moyenne, il lisse les pics.
- Météo-France (AROME, ARPEGE) n'a le vent que sur 17 % des heures testées dans les archives : il sert quand il est là mais n'est pas comparé seul ; ECMWF ne donne pas de rafales.

## Détail

### Vent moyen — Veille → lendemain, heure par heure (8882 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Erreur moy. corrigé | Biais corrigé |
|---|---|---|---|---|
| **Sous-modèle** | 0.59 | -0.04 | - | - |
| Moyenne simple des modèles | 0.84 | +0.05 | - | - |
| meteoswiss_icon_ch2 | 1.36 | +0.72 | 0.74 | -0.07 |
| meteoswiss_icon_seamless | 1.36 | +0.72 | 0.74 | -0.07 |
| icon_d2 | 1.25 | +0.66 | 0.74 | +0.01 |
| icon_seamless | 1.25 | +0.66 | 0.74 | +0.01 |
| icon_eu | 0.86 | -0.28 | 0.79 | -0.01 |
| gem_seamless | 1.13 | -1.04 | 0.79 | +0.01 |
| ecmwf_ifs025 | 1.08 | -0.95 | 0.80 | -0.05 |
| ecmwf_aifs025_single | 0.98 | -0.78 | 0.81 | -0.02 |
| knmi_harmonie_arome_europe | 1.60 | +1.03 | 0.81 | -0.00 |
| gfs_seamless | 0.93 | +0.04 | 0.84 | +0.05 |
| ukmo_seamless | 1.06 | -0.26 | 0.86 | +0.02 |

### Rafales — Veille → lendemain, heure par heure (8052 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Heures ≥ 10 m/s vues | Fausses alertes | Erreur moy. corrigé | Biais corrigé | Vues corrigé | Fausses alertes corrigé |
|---|---|---|---|---|---|---|---|---|
| **Sous-modèle** | 1.47 | -0.11 | 51 % | 29 % | - | - | - | - |
| Moyenne simple des modèles | 2.04 | -1.26 | 41 % | 28 % | - | - | - | - |
| meteoswiss_icon_ch2 | 2.28 | -0.49 | 73 % | 51 % | 1.77 | -0.13 | 23 % | 32 % |
| meteoswiss_icon_seamless | 2.28 | -0.49 | 73 % | 51 % | 1.77 | -0.13 | 23 % | 32 % |
| icon_d2 | 2.10 | -0.45 | 67 % | 49 % | 1.78 | +0.01 | 33 % | 34 % |
| icon_seamless | 2.10 | -0.45 | 67 % | 49 % | 1.78 | +0.01 | 33 % | 34 % |
| icon_eu | 2.23 | -1.39 | 29 % | 39 % | 1.91 | +0.01 | 26 % | 38 % |
| knmi_harmonie_arome_europe | 2.83 | +0.71 | 78 % | 68 % | 2.02 | +0.02 | 10 % | 40 % |
| gem_seamless | 3.71 | -3.48 | 6 % | 39 % | 2.06 | +0.03 | 19 % | 39 % |
| gfs_seamless | 3.81 | -3.70 | 1 % | 12 % | 2.23 | +0.21 | 11 % | 56 % |
| ukmo_seamless | 2.47 | -1.65 | 23 % | 34 % | 2.41 | -0.04 | 0 % | - |

### Vent moyen — Tendance (modèles globaux), J+1 (8942 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Erreur moy. corrigé | Biais corrigé |
|---|---|---|---|---|
| **Sous-modèle** | 0.59 | -0.04 | - | - |
| Moyenne simple des modèles | 0.77 | -0.24 | - | - |
| meteoswiss_icon_seamless | 1.36 | +0.72 | 0.74 | -0.07 |
| icon_seamless | 1.24 | +0.66 | 0.74 | +0.01 |
| icon_eu | 0.86 | -0.28 | 0.79 | -0.00 |
| gem_seamless | 1.13 | -1.03 | 0.79 | +0.01 |
| ecmwf_ifs025 | 1.08 | -0.95 | 0.80 | -0.05 |
| ecmwf_aifs025_single | 0.98 | -0.78 | 0.80 | -0.02 |
| gfs_seamless | 0.93 | +0.04 | 0.84 | +0.06 |
| ukmo_seamless | 1.06 | -0.26 | 0.86 | +0.02 |

### Rafales — Tendance (modèles globaux), J+1 (8052 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Heures ≥ 10 m/s vues | Fausses alertes | Erreur moy. corrigé | Biais corrigé | Vues corrigé | Fausses alertes corrigé |
|---|---|---|---|---|---|---|---|---|
| **Sous-modèle** | 1.47 | -0.12 | 52 % | 29 % | - | - | - | - |
| Moyenne simple des modèles | 2.29 | -1.86 | 19 % | 23 % | - | - | - | - |
| meteoswiss_icon_seamless | 2.28 | -0.49 | 73 % | 51 % | 1.77 | -0.13 | 23 % | 32 % |
| icon_seamless | 2.10 | -0.45 | 67 % | 49 % | 1.78 | +0.01 | 33 % | 34 % |
| icon_eu | 2.23 | -1.39 | 29 % | 39 % | 1.91 | +0.01 | 26 % | 38 % |
| gem_seamless | 3.71 | -3.48 | 6 % | 39 % | 2.06 | +0.03 | 19 % | 39 % |
| gfs_seamless | 3.81 | -3.70 | 1 % | 12 % | 2.23 | +0.21 | 11 % | 56 % |
| ukmo_seamless | 2.47 | -1.65 | 23 % | 34 % | 2.41 | -0.04 | 0 % | - |

### Vent moyen — Tendance (modèles globaux), J+3 (8622 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Erreur moy. corrigé | Biais corrigé |
|---|---|---|---|---|
| **Sous-modèle** | 0.66 | -0.08 | - | - |
| Moyenne simple des modèles | 0.80 | -0.37 | - | - |
| meteoswiss_icon_seamless | 1.37 | +0.68 | 0.76 | -0.08 |
| ecmwf_aifs025_single | 0.99 | -0.80 | 0.80 | -0.03 |
| ecmwf_ifs025 | 1.10 | -0.98 | 0.80 | -0.05 |
| gem_seamless | 1.14 | -1.04 | 0.81 | +0.01 |
| icon_seamless | 0.90 | -0.30 | 0.81 | -0.00 |
| icon_eu | 0.90 | -0.30 | 0.81 | -0.00 |
| gfs_seamless | 0.95 | +0.04 | 0.85 | +0.06 |
| ukmo_seamless | 1.07 | -0.28 | 0.87 | +0.05 |

### Rafales — Tendance (modèles globaux), J+3 (8120 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Heures ≥ 10 m/s vues | Fausses alertes | Erreur moy. corrigé | Biais corrigé | Vues corrigé | Fausses alertes corrigé |
|---|---|---|---|---|---|---|---|---|
| **Sous-modèle** | 1.68 | -0.16 | 37 % | 33 % | - | - | - | - |
| Moyenne simple des modèles | 2.47 | -2.06 | 10 % | 29 % | - | - | - | - |
| meteoswiss_icon_seamless | 2.42 | -0.55 | 65 % | 55 % | 1.88 | -0.13 | 12 % | 44 % |
| icon_seamless | 2.35 | -1.43 | 26 % | 44 % | 2.00 | +0.04 | 21 % | 40 % |
| icon_eu | 2.35 | -1.43 | 26 % | 44 % | 2.00 | +0.04 | 21 % | 40 % |
| gem_seamless | 3.77 | -3.56 | 6 % | 35 % | 2.08 | +0.01 | 13 % | 44 % |
| gfs_seamless | 3.85 | -3.73 | 0 % | 67 % | 2.26 | +0.21 | 9 % | 54 % |
| ukmo_seamless | 2.52 | -1.69 | 19 % | 39 % | 2.40 | +0.01 | 0 % | - |

### Vent moyen — Tendance (modèles globaux), J+5 (7856 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Erreur moy. corrigé | Biais corrigé |
|---|---|---|---|---|
| **Sous-modèle** | 0.74 | -0.06 | - | - |
| Moyenne simple des modèles | 0.90 | -0.59 | - | - |
| ecmwf_aifs025_single | 1.03 | -0.83 | 0.83 | -0.06 |
| ecmwf_ifs025 | 1.14 | -1.01 | 0.83 | -0.07 |
| icon_seamless | 0.97 | -0.23 | 0.84 | +0.01 |
| gem_seamless | 1.17 | -1.07 | 0.85 | +0.00 |
| gfs_seamless | 1.01 | -0.02 | 0.87 | +0.04 |
| ukmo_seamless | 1.13 | -0.38 | 0.88 | +0.03 |

### Rafales — Tendance (modèles globaux), J+5 (8559 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Heures ≥ 10 m/s vues | Fausses alertes | Erreur moy. corrigé | Biais corrigé | Vues corrigé | Fausses alertes corrigé |
|---|---|---|---|---|---|---|---|---|
| **Sous-modèle** | 1.89 | -0.11 | 25 % | 43 % | - | - | - | - |
| Moyenne simple des modèles | 2.57 | -1.73 | 13 % | 43 % | - | - | - | - |
| gem_seamless | 3.83 | -3.58 | 5 % | 37 % | 2.19 | +0.07 | 8 % | 41 % |
| icon_seamless | 3.54 | +2.13 | 67 % | 77 % | 2.22 | +0.15 | 7 % | 49 % |
| gfs_seamless | 3.86 | -3.75 | 0 % | 50 % | 2.26 | +0.20 | 4 % | 58 % |

### Vent moyen — Tendance (modèles globaux), J+7 (8825 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Erreur moy. corrigé | Biais corrigé |
|---|---|---|---|---|
| **Sous-modèle** | 0.78 | -0.07 | - | - |
| Moyenne simple des modèles | 0.95 | -0.71 | - | - |
| ecmwf_aifs025_single | 1.05 | -0.82 | 0.84 | -0.04 |
| ecmwf_ifs025 | 1.14 | -0.97 | 0.85 | -0.01 |
| gem_seamless | 1.16 | -1.03 | 0.86 | +0.03 |
| gfs_seamless | 1.03 | -0.01 | 0.88 | +0.06 |

### Rafales — Tendance (modèles globaux), J+7 (8823 heures testées)

| Prévision | Erreur moy. (m/s) | Biais | Heures ≥ 10 m/s vues | Fausses alertes | Erreur moy. corrigé | Biais corrigé | Vues corrigé | Fausses alertes corrigé |
|---|---|---|---|---|---|---|---|---|
| **Sous-modèle** | 2.04 | -0.20 | 10 % | 42 % | - | - | - | - |
| Moyenne simple des modèles | 3.77 | -3.63 | 0 % | 100 % | - | - | - | - |
| gem_seamless | 3.86 | -3.50 | 2 % | 68 % | 2.27 | +0.10 | 1 % | 72 % |
| gfs_seamless | 3.89 | -3.76 | 0 % | 100 % | 2.33 | +0.20 | 1 % | 74 % |

Durée du calcul : 9 min.
