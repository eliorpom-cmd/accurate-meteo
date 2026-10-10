# Modèles figés

Test honnête : entraîné avant le 2025-10-01, noté du 2025-10-01 au 2026-10-08, comparé au meilleur modèle météo seul sur les mêmes cas. Puis réentraîné sur toute la période.

| Modèle figé | Mesure | Figé | Meilleur modèle seul | Cas testés |
|---|---|---|---|---|
| heure_condition | condition /100 | **87.9** | 84.8 (ecmwf_ifs025) | 3697 |
| heure_pluie | réussite pluie % | **49.1** | 45.7 (icon_eu) | 8920 |
| heure_temperature | erreur moyenne | **1.05** | 1.45 (icon_eu) | 8950 |
| heure_vent | erreur moyenne | **0.65** | 0.86 (icon_eu) | 8942 |
| heure_rafales | erreur moyenne | **1.59** | 2.07 (icon_d2) | 8940 |
| bloc1_condition | condition /100 | **90.7** | 87.7 (icon_seamless) | 741 |
| bloc1_temperature | erreur moyenne | **0.91** | 1.09 (icon_seamless) | 745 |
| bloc1_rafales | erreur moyenne | **1.53** | 2.22 (icon_seamless) | 743 |
| bloc2_condition | condition /100 | **88.7** | 84.8 (ecmwf_ifs025) | 741 |
| bloc2_temperature | erreur moyenne | **1.04** | 1.19 (meteoswiss_icon_seamless) | 745 |
| bloc2_rafales | erreur moyenne | **1.67** | 2.63 (meteoswiss_icon_seamless) | 743 |
| bloc3_condition | condition /100 | **86.5** | 84.1 (meteoswiss_icon_seamless) | 741 |
| bloc3_temperature | erreur moyenne | **1.16** | 1.29 (meteoswiss_icon_seamless) | 745 |
| bloc3_rafales | erreur moyenne | **1.79** | 2.73 (meteoswiss_icon_seamless) | 743 |
| bloc4_condition | condition /100 | **84.2** | 80.0 (meteoswiss_icon_seamless) | 741 |
| bloc4_temperature | erreur moyenne | **1.28** | 1.49 (meteoswiss_icon_seamless) | 745 |
| bloc4_rafales | erreur moyenne | **1.82** | 2.84 (meteoswiss_icon_seamless) | 743 |
| bloc5_condition | condition /100 | **79.6** | 77.3 (ecmwf_ifs025) | 741 |
| bloc5_temperature | erreur moyenne | **1.45** | 1.89 (ecmwf_ifs025) | 745 |
| bloc5_rafales | erreur moyenne | **2.02** | 3.51 (icon_seamless) | 743 |
| bloc6_condition | condition /100 | **78.6** | 73.3 (ecmwf_ifs025) | 741 |
| bloc6_temperature | erreur moyenne | **1.75** | 2.15 (ukmo_seamless) | 745 |
| bloc6_rafales | erreur moyenne | **2.04** | 3.12 (ukmo_seamless) | 743 |
| bloc7_condition | condition /100 | **76.2** | 71.5 (ecmwf_ifs025) | 730 |
| bloc7_temperature | erreur moyenne | **2.38** | 2.46 (ecmwf_ifs025) | 734 |
| bloc7_rafales | erreur moyenne | **2.26** | 4.92 (gem_seamless) | 732 |
| pluie2h | réussite pluie % | **55.8** | 51.0 (icon_d2) | 26608 |
