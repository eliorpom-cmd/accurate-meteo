# Points voisins (roadmap 3b)

Chaque modèle lu aussi en 8 points autour de Grenoble (15km_0, 15km_90, 15km_180, 15km_270, 30km_45, 30km_135, 30km_225, 30km_315), modèles icon_eu, meteofrance_arome_france, meteofrance_seamless, ecmwf_ifs025, icon_seamless, variables shortwave_radiation,cloud_cover,precipitation. Test honnête : entraîné avant le 2025-10-01, noté après, mêmes cas avec et sans voisins.

| Modèle | Sans voisins | Avec voisins | Écart | Cas testés |
|---|---|---|---|---|
| heure_condition (veille) | 87.9 | **88.4** | +0.6 | 3697 |
| heure_pluie (veille, réussite %) | 49.1 | **51.3** | +2.2 | 8920 |
| bloc1_condition (J+1) | 90.8 | **91.0** | +0.2 | 741 |
| bloc2_condition (J+2) | 88.7 | **88.2** | -0.5 | 741 |

## Test mois par mois

Chaque mois laissé de côté à tour de rôle (entraîné sur tous les autres), comme retro.py. « Mois gagnés » = mois où les voisins font mieux, sur les mois où il y a un écart.

| Modèle | Sans voisins | Avec voisins | Écart | Mois gagnés | Cas testés |
|---|---|---|---|---|---|
| heure_condition (veille) | 85.3 | **85.3** | +0.1 | 15 / 31 | 10085 |
| heure_pluie (veille, réussite %) | 43.6 | **44.3** | +0.7 | 18 / 33 | 23489 |
| bloc1_condition (J+1) | 88.3 | **88.2** | -0.1 | 14 / 29 | 1954 |
| bloc2_condition (J+2) | 85.6 | **85.5** | -0.1 | 11 / 28 | 1954 |

**Conclusion (10/10/2026)** : le gain du premier test venait surtout de la période testée. Mois par mois, les voisins ne changent rien au ciel ni aux demi-journées, et apportent +0,7 point sur la pluie heure par heure (18 mois sur 33). Pas mis en production.
