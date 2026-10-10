# Sous-modèle température

Cible : température à 2 m mesurée à GRENOBLE-CEA-RADOME, heure par heure. Test honnête : chaque mois de 2025-10-01 au 2026-10-08 est prédit par un modèle entraîné sur tous les autres mois (données depuis le 2024-02-01). Toutes les prévisions sont notées sur exactement les mêmes heures.

Sous-modèle : gradient boosting (scikit-learn, 300 arbres) avec la température et les autres paramètres (humidité, vent, rafales, direction, pression, soleil, nuages, pluie) de chaque modèle, l'heure, la saison, et ce qui était observé à la station au moment de la prévision (échéance + 6 h avant) : température, humidité, vent, pression, température à la même heure la veille, erreur récente de la moyenne des modèles.

Correction de biais : chaque modèle moins son erreur moyenne apprise sur les mois d'entraînement.

## 1. La veille pour le lendemain (J+1), heure par heure

Modèles comparés : meteofrance_arome_france, meteofrance_seamless, meteofrance_arpege_europe, icon_d2, icon_eu, icon_seamless, meteoswiss_icon_ch2, meteoswiss_icon_seamless, ecmwf_ifs025, ecmwf_aifs025_single, ukmo_seamless, gfs_seamless, gem_seamless, knmi_harmonie_arome_europe.

### Toutes les heures testées (8005 heures)

| Prévision | Erreur moyenne | Biais | à ±1 °C | à ±2 °C |
|---|---|---|---|---|
| **sous-modèle (squared_error)** | 1.02 °C | +0.04 °C | 61 % | 88 % |
| **sous-modèle (absolute_error)** | 1.03 °C | +0.08 °C | 60 % | 87 % |
| moyenne des modèles (biais corrigés) | 1.24 °C | +0.08 °C | 50 % | 81 % |
| moyenne des modèles | 1.24 °C | +0.27 °C | 50 % | 81 % |
| meteoswiss_icon_ch2 (biais corrigé) | 1.40 °C | +0.01 °C | 45 % | 76 % |
| meteoswiss_icon_seamless (biais corrigé) | 1.40 °C | +0.01 °C | 45 % | 76 % |
| icon_seamless (biais corrigé) | 1.43 °C | +0.31 °C | 44 % | 75 % |
| icon_d2 (biais corrigé) | 1.43 °C | +0.31 °C | 44 % | 75 % |
| icon_eu (biais corrigé) | 1.45 °C | +0.11 °C | 42 % | 75 % |
| meteofrance_arome_france (biais corrigé) | 1.46 °C | +0.05 °C | 44 % | 74 % |
| icon_eu | 1.48 °C | +0.54 °C | 46 % | 75 % |
| meteoswiss_icon_ch2 | 1.52 °C | +0.86 °C | 45 % | 75 % |
| meteoswiss_icon_seamless | 1.52 °C | +0.86 °C | 45 % | 75 % |
| ukmo_seamless | 1.53 °C | -0.15 °C | 45 % | 75 % |
| meteofrance_seamless (biais corrigé) | 1.54 °C | +0.01 °C | 42 % | 72 % |
| ukmo_seamless (biais corrigé) | 1.54 °C | +0.02 °C | 43 % | 74 % |
| meteofrance_arome_france | 1.55 °C | +0.85 °C | 46 % | 73 % |
| ecmwf_aifs025_single (biais corrigé) | 1.55 °C | +0.07 °C | 40 % | 71 % |
| meteofrance_seamless | 1.56 °C | +0.56 °C | 45 % | 72 % |
| icon_seamless | 1.56 °C | +0.90 °C | 43 % | 72 % |
| icon_d2 | 1.56 °C | +0.90 °C | 43 % | 72 % |
| meteofrance_arpege_europe (biais corrigé) | 1.56 °C | +0.13 °C | 42 % | 71 % |
| ecmwf_ifs025 (biais corrigé) | 1.61 °C | -0.29 °C | 41 % | 70 % |
| meteofrance_arpege_europe | 1.68 °C | +0.90 °C | 42 % | 69 % |
| gem_seamless | 1.72 °C | +0.22 °C | 42 % | 69 % |
| gem_seamless (biais corrigé) | 1.74 °C | -0.09 °C | 39 % | 67 % |
| knmi_harmonie_arome_europe (biais corrigé) | 1.75 °C | +0.28 °C | 37 % | 66 % |
| ecmwf_ifs025 | 1.82 °C | -1.05 °C | 36 % | 65 % |
| knmi_harmonie_arome_europe | 1.88 °C | +1.04 °C | 38 % | 64 % |
| gfs_seamless (biais corrigé) | 1.98 °C | +0.18 °C | 35 % | 60 % |
| gfs_seamless | 2.00 °C | -0.36 °C | 34 % | 60 % |
| ecmwf_aifs025_single | 2.61 °C | -2.34 °C | 19 % | 40 % |

### J+1 : erreur moyenne par saison

| Prévision | toutes (8005 h) | hiver (DJF) (2160 h) | été (JJA) (2089 h) | matins d'hiver 6-9 h (360 h) |
|---|---|---|---|---|
| **sous-modèle (squared_error)** | 1.02 | 1.17 | 1.05 | 1.10 |
| icon_eu | 1.48 | 1.61 | 1.65 | 1.60 |
| meteoswiss_icon_ch2 (biais corrigé) | 1.40 | 1.38 | 1.49 | 1.40 |
| moyenne des modèles | 1.24 | 1.27 | 1.38 | 1.17 |
| moyenne des modèles (biais corrigés) | 1.24 | 1.25 | 1.36 | 1.11 |

### Sur quoi s'appuie le sous-modèle (J+1, janvier 2026)

Hausse de l'erreur moyenne quand on brouille toutes les colonnes d'un modèle (erreur de départ 1.36 °C) :

| Source | Hausse de l'erreur |
|---|---|
| icon_d2 | +0.86 °C |
| meteofrance_arome_france | +0.49 °C |
| ecmwf_ifs025 | +0.13 °C |
| icon_eu | +0.10 °C |
| observations à la station | +0.08 °C |
| meteofrance_arpege_europe | +0.07 °C |
| meteofrance_seamless | +0.07 °C |
| gem_seamless | +0.07 °C |
| ukmo_seamless | +0.06 °C |
| heure + saison | +0.04 °C |
| gfs_seamless | +0.03 °C |
| knmi_harmonie_arome_europe | +0.03 °C |
| icon_seamless | +0.02 °C |
| ecmwf_aifs025_single | +0.02 °C |
| meteoswiss_icon_ch2 | +0.01 °C |
| meteoswiss_icon_seamless | +0.00 °C |

## 2. De J+1 à J+7, heure par heure

Modèles : ecmwf_ifs025, ecmwf_aifs025_single, icon_seamless, icon_eu, meteoswiss_icon_seamless, gfs_seamless, gem_seamless, ukmo_seamless, meteofrance_seamless. Perte du sous-modèle : squared_error (meilleure à J+1).

Erreur moyenne (°C) selon le nombre de jours d'avance, chaque échéance notée sur ses heures communes :

| | J+1 | J+2 | J+3 | J+4 | J+5 | J+6 | J+7 |
|---|---|---|---|---|---|---|---|
| **sous-modèle, un modèle par échéance** | 1.03 | 1.12 | 1.24 | 1.41 | 1.59 | 1.80 | 2.00 |
| **sous-modèle, un modèle pour toutes** | 1.21 | 1.22 | 1.33 | 1.44 | 1.57 | 1.79 | 1.99 |
| meilleur modèle seul | 1.48 (icon_eu) | 1.51 (icon_seamless) | 1.61 (icon_seamless) | 1.82 (meteoswiss_icon_seamless) | 2.16 (gem_seamless) | 2.34 (ukmo_seamless) | 2.63 (gem_seamless) |
| meilleur modèle seul, biais corrigé | 1.40 (meteoswiss_icon_seamless) | 1.42 (meteoswiss_icon_seamless) | 1.54 (meteoswiss_icon_seamless) | 1.68 (meteoswiss_icon_seamless) | 1.93 (ecmwf_aifs025_single) | 2.04 (ecmwf_aifs025_single) | 2.24 (ecmwf_aifs025_single) |
| moyenne des modèles | 1.24 | 1.31 | 1.41 | 1.56 | 1.89 | 2.01 | 2.27 |
| moyenne, biais corrigés | 1.24 | 1.30 | 1.40 | 1.53 | 1.77 | 1.92 | 2.06 |
| heures testées | 8061 | 8950 | 8138 | 7849 | 8555 | 8018 | 8632 |

### J+3, détail (8138 heures)

| Prévision | Erreur moyenne | Biais | à ±1 °C | à ±2 °C |
|---|---|---|---|---|
| **sous-modèle, un par échéance** | 1.24 °C | +0.00 °C | 52 % | 81 % |
| **sous-modèle, un pour toutes** | 1.33 °C | -0.14 °C | 49 % | 79 % |
| moyenne des modèles (biais corrigés) | 1.40 °C | +0.01 °C | 45 % | 76 % |
| moyenne des modèles | 1.41 °C | -0.13 °C | 45 % | 75 % |
| meteoswiss_icon_seamless (biais corrigé) | 1.54 °C | -0.02 °C | 42 % | 72 % |
| icon_seamless (biais corrigé) | 1.58 °C | +0.15 °C | 41 % | 70 % |
| icon_eu (biais corrigé) | 1.58 °C | +0.15 °C | 41 % | 70 % |
| icon_seamless | 1.61 °C | +0.51 °C | 43 % | 71 % |

### J+7, détail (8632 heures)

| Prévision | Erreur moyenne | Biais | à ±1 °C | à ±2 °C |
|---|---|---|---|---|
| **sous-modèle, un pour toutes** | 1.99 °C | -0.15 °C | 33 % | 60 % |
| **sous-modèle, un par échéance** | 2.00 °C | -0.13 °C | 33 % | 61 % |
| moyenne des modèles (biais corrigés) | 2.06 °C | -0.04 °C | 33 % | 58 % |
| ecmwf_aifs025_single (biais corrigé) | 2.24 °C | +0.03 °C | 30 % | 55 % |
| moyenne des modèles | 2.27 °C | -1.12 °C | 28 % | 54 % |
| ecmwf_ifs025 (biais corrigé) | 2.60 °C | -0.14 °C | 25 % | 48 % |
| gem_seamless | 2.63 °C | -0.26 °C | 27 % | 49 % |
| gem_seamless (biais corrigé) | 2.63 °C | -0.13 °C | 26 % | 49 % |

## Conclusions

- La veille pour le lendemain, le sous-modèle se trompe en moyenne de 1,02 °C, contre 1,40 °C pour le meilleur modèle seul corrigé de son biais (MeteoSwiss ICON) et 1,24 °C pour la moyenne des modèles : 27 % d'erreur en moins que le meilleur modèle, 18 % de moins que la moyenne. 61 % des heures à ±1 °C contre 45 % et 50 %.
- Le gain reste net jusqu'à J+4 (1,41 contre 1,53 pour la moyenne corrigée), puis se réduit : à J+7, 2,00 contre 2,06.
- Un modèle par échéance est meilleur de J+1 à J+3 (1,03 contre 1,21 à J+1) ; au-delà, un seul modèle pour toutes les échéances fait aussi bien. Perte « carrée » ou « absolue » : même résultat (1,02 contre 1,03).
- Le sous-modèle s'appuie surtout sur ICON-D2 et AROME, puis ECMWF IFS et ICON-EU ; les observations du moment comptent peu (+0,08 °C si on les retire). ICON-D2 et ICON seamless donnent les mêmes valeurs à J+1 (comme MeteoSwiss CH2 et MeteoSwiss seamless) : leur part est partagée au hasard entre les deux.
- Le gain dépend de la saison : 0,31 °C de mieux que la moyenne corrigée en été (1,05 contre 1,36), 0,08 °C en hiver (1,17 contre 1,25), et rien les matins d'hiver de 6 à 9 h, quand l'air froid stagne au fond de la vallée (1,10 contre 1,11).

Note : à chaque échéance, les heures testées sont celles où tous les modèles comparés ont une valeur ; leur nombre varie donc un peu d'une échéance à l'autre (7 849 à 8 950).

_Calcul : 14 min._
