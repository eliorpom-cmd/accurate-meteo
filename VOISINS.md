# Points voisins (roadmap 3b)

Chaque modèle lu aussi en 8 points autour de Grenoble (15km_0, 15km_90, 15km_180, 15km_270, 30km_45, 30km_135, 30km_225, 30km_315), modèles icon_eu, meteofrance_arome_france, meteofrance_seamless, ecmwf_ifs025, icon_seamless, variables shortwave_radiation,cloud_cover,precipitation. Test honnête : entraîné avant le 2025-10-01, noté après, mêmes cas avec et sans voisins.

| Modèle | Sans voisins | Avec voisins | Écart | Cas testés |
|---|---|---|---|---|
| heure_condition (veille) | 87.9 | **88.4** | +0.6 | 3697 |
| heure_pluie (veille, réussite %) | 49.1 | **51.3** | +2.2 | 8920 |
| bloc1_condition (J+1) | 90.8 | **91.0** | +0.2 | 741 |
| bloc2_condition (J+2) | 88.7 | **88.2** | -0.5 | 741 |
