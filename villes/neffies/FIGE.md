# Modèles figés

Test honnête : entraîné avant le 2026-04-01, noté du 2026-04-01 au 2026-10-20, comparé au meilleur modèle météo seul sur les mêmes cas. Puis réentraîné sur toute la période.

| Modèle figé | Mesure | Figé | Meilleur modèle seul | Cas testés |
|---|---|---|---|---|
| heure_condition | condition /100 | **92.7** | 90.8 (icon_d2) | 2385 |
| heure_pluie | réussite pluie % | **30.7** | 29.5 (ukmo_seamless) | 4872 |
| heure_temperature | erreur moyenne | **1.07** | 1.06 (icon_seamless) | 4865 |
| heure_vent | erreur moyenne | **0.69** | 0.83 (icon_d2) | 4869 |
| heure_rafales | erreur moyenne | **1.16** | 1.43 (icon_eu) | 4872 |
| bloc1_condition | condition /100 | **94.3** | 92.0 (meteofrance_seamless) | 406 |
| bloc1_temperature | erreur moyenne | **0.75** | 0.76 (meteofrance_seamless) | 403 |
| bloc1_rafales | erreur moyenne | **1.14** | 1.39 (icon_eu) | 406 |
| bloc2_condition | condition /100 | **92.1** | 90.5 (gem_seamless) | 406 |
| bloc2_temperature | erreur moyenne | **0.87** | 0.93 (icon_seamless) | 403 |
| bloc2_rafales | erreur moyenne | **1.28** | 1.55 (icon_eu) | 406 |
| bloc3_condition | condition /100 | **92.3** | 89.1 (meteoswiss_icon_seamless) | 406 |
| bloc3_temperature | erreur moyenne | **0.88** | 0.99 (ecmwf_ifs025) | 403 |
| bloc3_rafales | erreur moyenne | **1.34** | 1.67 (icon_seamless) | 406 |
| bloc4_condition | condition /100 | **89.3** | 88.3 (meteoswiss_icon_seamless) | 406 |
| bloc4_temperature | erreur moyenne | **1.08** | 1.14 (ecmwf_ifs025) | 403 |
| bloc4_rafales | erreur moyenne | **1.61** | 1.90 (meteoswiss_icon_seamless) | 406 |
| bloc5_condition | condition /100 | **88.3** | 84.9 (ecmwf_aifs025_single) | 406 |
| bloc5_temperature | erreur moyenne | **1.28** | 1.50 (ecmwf_ifs025) | 403 |
| bloc5_rafales | erreur moyenne | **1.66** | 2.23 (icon_seamless) | 406 |
| bloc6_condition | condition /100 | **86.0** | 83.8 (ecmwf_ifs025) | 406 |
| bloc6_temperature | erreur moyenne | **1.45** | 1.79 (ecmwf_ifs025) | 403 |
| bloc6_rafales | erreur moyenne | **1.92** | 2.55 (icon_seamless) | 406 |
| bloc7_condition | condition /100 | **87.2** | 83.7 (gem_seamless) | 395 |
| bloc7_temperature | erreur moyenne | **1.70** | 2.01 (ecmwf_ifs025) | 392 |
| bloc7_rafales | erreur moyenne | **2.09** | 3.47 (gem_seamless) | 395 |
| pluie2h | réussite pluie % | **36.8** | 38.0 (meteofrance_seamless) | 14616 |
