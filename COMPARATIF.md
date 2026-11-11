# GRESIL en direct contre chaque modèle météo — Grenoble

Prévisions de GRESIL réellement publiées (journal de production, 775 enregistrements du 09/10/2026 16 h UTC au 11/11/2026 08 h UTC), comparées à ce que chaque modèle météo annonçait avec la même avance (Open-Meteo Previous Runs) et à la station GRENOBLE-CEA-RADOME (dernière mesure : 11/11/2026 04 h UTC ; ciel : satellite). Tous notés sur les mêmes cas. Rien n'est rejoué pour GRESIL.

## Résumé

« Meilleur modèle seul » = le meilleur des modèles sur cette ligne, choisi après coup (avantage aux modèles). Écart : positif = GRESIL meilleur ; entre crochets, intervalle à 90 % par tirage de jours entiers. « Bat » = nombre de modèles que GRESIL dépasse.

| Échéance | Variable | GRESIL | Meilleur modèle seul | Écart [90 %] | Bat | Cas | Verdict |
|---|---|---|---|---|---|---|---|
| Veille, heure par heure | Ciel /100 | 84,3 | 83,6 (ecmwf_ifs025) | +0,7 [-3,5 ; 5,0] | 14/14 | 258 (31 j) | pas de différence sûre |
| Veille, heure par heure | Pluie, réussite % | 48,4 | 42,1 (ukmo_seamless) | +6,3 [-3,3 ; 16,1] | 14/14 | 736 (32 j), 75 avec pluie | pas de différence sûre |
| Veille, heure par heure | Température, erreur °C | 1,29 | 1,27 (meteoswiss_icon_ch2) | −0,03 [-0,16 ; 0,11] | 12/14 | 736 (32 j) | pas de différence sûre |
| Veille, heure par heure | Vent, erreur m/s | 0,65 | 0,91 (gfs_seamless) | +0,26 [0,20 ; 0,32] | 14/14 | 736 (32 j) | GRESIL meilleur |
| Veille, heure par heure | Rafales, erreur m/s | 1,53 | 2,13 (meteoswiss_icon_ch2) | +0,60 [0,42 ; 0,76] | 12/12 | 736 (32 j) | GRESIL meilleur |
| Demi-journées J+1 | Ciel /100 | 87,6 | 81,9 (meteoswiss_icon_seamless) | +5,6 [-0,0 ; 11,3] | 9/9 | 62 (31 j) | pas de différence sûre |
| Demi-journées J+1 | Température, erreur °C | 0,87 | 1,11 (icon_seamless) | +0,24 [0,04 ; 0,45] | 9/9 | 62 (31 j) | GRESIL meilleur |
| Demi-journées J+2 | Ciel /100 | 81,0 | 79,5 (gfs_seamless) | +1,5 [-5,5 ; 8,5] | 9/9 | 60 (30 j) | pas de différence sûre |
| Demi-journées J+2 | Température, erreur °C | 1,15 | 1,12 (icon_seamless) | −0,03 [-0,26 ; 0,20] | 7/9 | 60 (30 j) | pas de différence sûre |
| Demi-journées J+3 | Ciel /100 | 72,6 | 77,1 (icon_seamless) | −4,5 [-14,0 ; 4,1] | 4/9 | 58 (29 j) | pas de différence sûre |
| Demi-journées J+3 | Température, erreur °C | 1,26 | 1,07 (icon_seamless) | −0,19 [-0,38 ; 0,00] | 6/9 | 58 (29 j) | pas de différence sûre |
| Demi-journées J+4 | Ciel /100 | 73,5 | 76,7 (ecmwf_ifs025) | −3,3 [-13,1 ; 6,4] | 7/8 | 55 (28 j) | pas de différence sûre |
| Demi-journées J+4 | Température, erreur °C | 1,30 | 1,25 (meteoswiss_icon_seamless) | −0,05 [-0,29 ; 0,20] | 7/8 | 55 (28 j) | pas de différence sûre |
| Demi-journées J+5 | Ciel /100 | 58,9 | 69,6 (icon_seamless) | −10,7 [-23,5 ; 1,9] | 2/6 | 54 (27 j) | pas de différence sûre |
| Demi-journées J+5 | Température, erreur °C | 1,84 | 1,69 (ecmwf_ifs025) | −0,15 [-0,54 ; 0,24] | 3/6 | 54 (27 j) | pas de différence sûre |
| Demi-journées J+6 | Ciel /100 | 63,1 | 57,7 (gem_seamless) | +5,4 [-1,9 ; 12,5] | 6/6 | 52 (26 j) | pas de différence sûre |
| Demi-journées J+6 | Température, erreur °C | 1,86 | 1,68 (ecmwf_aifs025_single) | −0,18 [-0,73 ; 0,35] | 5/6 | 52 (26 j) | pas de différence sûre |
| Demi-journées J+7 | Ciel /100 | 53,0 | 56,0 (ecmwf_ifs025) | −3,0 [-15,0 ; 9,0] | 3/4 | 50 (25 j) | pas de différence sûre |
| Demi-journées J+7 | Température, erreur °C | 1,65 | 1,71 (ecmwf_aifs025_single) | +0,05 [-0,44 ; 0,53] | 4/4 | 50 (25 j) | pas de différence sûre |
| 2 prochaines heures | Pluie, réussite % | 54,8 | 47,2 (meteoswiss_icon_ch1) | +7,6 [2,0 ; 14,8] | 8/8 | 4488 (34 j), 300 avec pluie | GRESIL meilleur |

Ciel = soleil / mitigé / couvert / pluie, de jour seulement, crédit partiel entre catégories voisines. Réussite pluie = cas de pluie bien annoncés / (bien annoncés + manqués + fausses alertes) ; pluie = au moins 0.2 mm dans l'heure, 0.05 mm par tranche de 20 min.

## Contre quatre modèles connus, un par un

Météo-France (meteofrance_seamless), ECMWF IFS (européen), ICON (allemand, icon_seamless), GFS (américain). Mêmes cas que le résumé, même lecture de l'écart.

| Échéance | Variable | Modèle | GRESIL | Modèle | Écart [90 %] | Verdict |
|---|---|---|---|---|---|---|
| Veille, heure par heure | Ciel /100 | meteofrance_seamless | 84,3 | 73,4 | +10,9 [4,5 ; 18,0] | GRESIL meilleur |
| Veille, heure par heure | Ciel /100 | ecmwf_ifs025 | 84,3 | 83,6 | +0,7 [-3,5 ; 5,0] | pas de différence sûre |
| Veille, heure par heure | Ciel /100 | icon_seamless | 84,3 | 77,1 | +7,3 [2,8 ; 12,1] | GRESIL meilleur |
| Veille, heure par heure | Ciel /100 | gfs_seamless | 84,3 | 78,1 | +6,2 [1,1 ; 11,8] | GRESIL meilleur |
| Veille, heure par heure | Pluie, réussite % | meteofrance_seamless | 48,4 | 28,7 | +19,7 [7,0 ; 30,4] | GRESIL meilleur |
| Veille, heure par heure | Pluie, réussite % | ecmwf_ifs025 | 48,4 | 36,7 | +11,7 [2,6 ; 20,5] | GRESIL meilleur |
| Veille, heure par heure | Pluie, réussite % | icon_seamless | 48,4 | 31,5 | +16,9 [7,1 ; 25,8] | GRESIL meilleur |
| Veille, heure par heure | Pluie, réussite % | gfs_seamless | 48,4 | 39,3 | +9,1 [-1,7 ; 19,2] | pas de différence sûre |
| Veille, heure par heure | Température, erreur °C | meteofrance_seamless | 1,29 | 1,38 | +0,09 [-0,03 ; 0,21] | pas de différence sûre |
| Veille, heure par heure | Température, erreur °C | ecmwf_ifs025 | 1,29 | 1,51 | +0,22 [0,04 ; 0,39] | GRESIL meilleur |
| Veille, heure par heure | Température, erreur °C | icon_seamless | 1,29 | 1,44 | +0,15 [-0,02 ; 0,33] | pas de différence sûre |
| Veille, heure par heure | Température, erreur °C | gfs_seamless | 1,29 | 1,60 | +0,31 [0,13 ; 0,50] | GRESIL meilleur |
| Veille, heure par heure | Vent, erreur m/s | meteofrance_seamless | 0,65 | 1,47 | +0,82 [0,58 ; 1,08] | GRESIL meilleur |
| Veille, heure par heure | Vent, erreur m/s | ecmwf_ifs025 | 0,65 | 1,09 | +0,44 [0,34 ; 0,54] | GRESIL meilleur |
| Veille, heure par heure | Vent, erreur m/s | icon_seamless | 0,65 | 1,10 | +0,45 [0,32 ; 0,59] | GRESIL meilleur |
| Veille, heure par heure | Vent, erreur m/s | gfs_seamless | 0,65 | 0,91 | +0,26 [0,20 ; 0,32] | GRESIL meilleur |
| Veille, heure par heure | Rafales, erreur m/s | meteofrance_seamless | 1,53 | 2,16 | +0,63 [0,41 ; 0,85] | GRESIL meilleur |
| Veille, heure par heure | Rafales, erreur m/s | icon_seamless | 1,53 | 2,19 | +0,66 [0,49 ; 0,82] | GRESIL meilleur |
| Veille, heure par heure | Rafales, erreur m/s | gfs_seamless | 1,53 | 3,81 | +2,28 [1,97 ; 2,59] | GRESIL meilleur |
| Demi-journées J+1 | Ciel /100 | meteofrance_seamless | 87,6 | 77,1 | +10,5 [3,1 ; 18,1] | GRESIL meilleur |
| Demi-journées J+1 | Ciel /100 | ecmwf_ifs025 | 87,6 | 79,0 | +8,5 [3,7 ; 13,9] | GRESIL meilleur |
| Demi-journées J+1 | Ciel /100 | icon_seamless | 87,6 | 79,5 | +8,1 [1,6 ; 14,5] | GRESIL meilleur |
| Demi-journées J+1 | Ciel /100 | gfs_seamless | 87,6 | 78,4 | +9,2 [4,0 ; 14,5] | GRESIL meilleur |
| Demi-journées J+1 | Température, erreur °C | meteofrance_seamless | 0,87 | 1,19 | +0,32 [0,15 ; 0,49] | GRESIL meilleur |
| Demi-journées J+1 | Température, erreur °C | ecmwf_ifs025 | 0,87 | 1,24 | +0,37 [0,11 ; 0,65] | GRESIL meilleur |
| Demi-journées J+1 | Température, erreur °C | icon_seamless | 0,87 | 1,11 | +0,24 [0,04 ; 0,45] | GRESIL meilleur |
| Demi-journées J+1 | Température, erreur °C | gfs_seamless | 0,87 | 1,46 | +0,59 [0,26 ; 0,94] | GRESIL meilleur |
| Demi-journées J+3 | Ciel /100 | meteofrance_seamless | 72,6 | 68,8 | +3,8 [-5,2 ; 12,8] | pas de différence sûre |
| Demi-journées J+3 | Ciel /100 | ecmwf_ifs025 | 72,6 | 75,3 | −2,8 [-11,2 ; 5,5] | pas de différence sûre |
| Demi-journées J+3 | Ciel /100 | icon_seamless | 72,6 | 77,1 | −4,5 [-14,0 ; 4,1] | pas de différence sûre |
| Demi-journées J+3 | Ciel /100 | gfs_seamless | 72,6 | 73,3 | −0,7 [-8,5 ; 7,1] | pas de différence sûre |
| Demi-journées J+3 | Température, erreur °C | meteofrance_seamless | 1,26 | 1,54 | +0,28 [0,08 ; 0,50] | GRESIL meilleur |
| Demi-journées J+3 | Température, erreur °C | ecmwf_ifs025 | 1,26 | 1,32 | +0,06 [-0,16 ; 0,28] | pas de différence sûre |
| Demi-journées J+3 | Température, erreur °C | icon_seamless | 1,26 | 1,07 | −0,19 [-0,38 ; 0,00] | pas de différence sûre |
| Demi-journées J+3 | Température, erreur °C | gfs_seamless | 1,26 | 1,54 | +0,28 [-0,00 ; 0,55] | pas de différence sûre |
| Demi-journées J+5 | Ciel /100 | ecmwf_ifs025 | 58,9 | 62,0 | −3,1 [-13,7 ; 8,1] | pas de différence sûre |
| Demi-journées J+5 | Ciel /100 | icon_seamless | 58,9 | 69,6 | −10,7 [-23,5 ; 1,9] | pas de différence sûre |
| Demi-journées J+5 | Ciel /100 | gfs_seamless | 58,9 | 63,7 | −4,8 [-13,7 ; 4,1] | pas de différence sûre |
| Demi-journées J+5 | Température, erreur °C | ecmwf_ifs025 | 1,84 | 1,69 | −0,15 [-0,54 ; 0,24] | pas de différence sûre |
| Demi-journées J+5 | Température, erreur °C | icon_seamless | 1,84 | 1,75 | −0,09 [-0,51 ; 0,36] | pas de différence sûre |
| Demi-journées J+5 | Température, erreur °C | gfs_seamless | 1,84 | 2,27 | +0,43 [0,11 ; 0,73] | GRESIL meilleur |
| Demi-journées J+7 | Ciel /100 | ecmwf_ifs025 | 53,0 | 56,0 | −3,0 [-15,0 ; 9,0] | pas de différence sûre |
| Demi-journées J+7 | Ciel /100 | gfs_seamless | 53,0 | 45,8 | +7,2 [-7,4 ; 20,6] | pas de différence sûre |
| Demi-journées J+7 | Température, erreur °C | ecmwf_ifs025 | 1,65 | 1,98 | +0,33 [0,07 ; 0,58] | GRESIL meilleur |
| Demi-journées J+7 | Température, erreur °C | gfs_seamless | 1,65 | 2,95 | +1,30 [0,79 ; 1,78] | GRESIL meilleur |
| 2 prochaines heures | Pluie, réussite % | meteofrance_seamless | 54,8 | 43,6 | +11,3 [0,7 ; 16,9] | GRESIL meilleur |
| 2 prochaines heures | Pluie, réussite % | ecmwf_ifs025 | 54,8 | 30,2 | +24,7 [12,9 ; 33,3] | GRESIL meilleur |
| 2 prochaines heures | Pluie, réussite % | meteofrance_arome_france | 54,8 | 46,9 | +8,0 [-1,8 ; 16,1] | pas de différence sûre |
| 2 prochaines heures | Pluie, réussite % | icon_d2 | 54,8 | 45,6 | +9,3 [2,4 ; 14,0] | GRESIL meilleur |

## Veille pour le lendemain, heure par heure : tous les modèles

| Source | Ciel /100 | Pluie, réussite % | Température, erreur °C | Vent, erreur m/s | Rafales, erreur m/s |
|---|---|---|---|---|---|
| GRESIL | **84,3** | **48,4** | 1,29 | **0,65** | **1,53** |
| ecmwf_aifs025_single | 74,1 | 35,1 | 2,07 | 0,95 | - |
| ecmwf_ifs025 | 83,6 | 36,7 | 1,51 | 1,09 | - |
| gem_seamless | 75,5 | 31,7 | 1,48 | 1,11 | 4,03 |
| gfs_seamless | 78,1 | 39,3 | 1,60 | 0,91 | 3,81 |
| icon_d2 | 77,1 | 31,5 | 1,44 | 1,10 | 2,19 |
| icon_eu | 78,5 | 40,9 | 1,32 | 0,91 | 2,63 |
| icon_seamless | 77,1 | 31,5 | 1,44 | 1,10 | 2,19 |
| knmi_harmonie_arome_europe | 73,1 | 38,7 | 1,62 | 1,43 | 2,69 |
| meteofrance_arome_france | 73,0 | 30,0 | 1,35 | 1,17 | 2,20 |
| meteofrance_arpege_europe | 72,0 | 34,1 | 1,46 | 1,41 | 3,37 |
| meteofrance_seamless | 73,4 | 28,7 | 1,38 | 1,47 | 2,16 |
| meteoswiss_icon_ch2 | 80,5 | 40,0 | **1,27** | 1,08 | 2,13 |
| meteoswiss_icon_seamless | 80,5 | 40,0 | **1,27** | 1,08 | 2,13 |
| ukmo_seamless | 74,5 | 42,1 | 1,49 | 1,06 | 2,70 |

Cas notés : Ciel /100 258 ; Pluie, réussite % 736 ; Température, erreur °C 736 ; Vent, erreur m/s 736 ; Rafales, erreur m/s 736.
Écartés faute de données sur la période (au moins une variable) : ecmwf_aifs025_single, ecmwf_ifs025.

## Demi-journées J+1 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | **87,6** | **0,87** |
| ecmwf_aifs025_single | 68,7 | 1,91 |
| ecmwf_ifs025 | 79,0 | 1,24 |
| gem_seamless | 71,5 | 1,28 |
| gfs_seamless | 78,4 | 1,46 |
| icon_eu | 77,6 | 1,14 |
| icon_seamless | 79,5 | 1,11 |
| meteofrance_seamless | 77,1 | 1,19 |
| meteoswiss_icon_seamless | 81,9 | 1,17 |
| ukmo_seamless | 76,5 | 1,31 |

Cas notés : Ciel /100 62 ; Température, erreur °C 62.

## Demi-journées J+2 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | **81,0** | 1,15 |
| ecmwf_aifs025_single | 68,2 | 1,97 |
| ecmwf_ifs025 | 76,8 | 1,25 |
| gem_seamless | 69,5 | 1,21 |
| gfs_seamless | 79,5 | 1,35 |
| icon_eu | 73,2 | **1,12** |
| icon_seamless | 73,2 | **1,12** |
| meteofrance_seamless | 71,8 | 1,39 |
| meteoswiss_icon_seamless | 77,3 | 1,29 |
| ukmo_seamless | 69,5 | 1,41 |

Cas notés : Ciel /100 60 ; Température, erreur °C 60.

## Demi-journées J+3 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | 72,6 | 1,26 |
| ecmwf_aifs025_single | 67,9 | 1,90 |
| ecmwf_ifs025 | 75,3 | 1,32 |
| gem_seamless | 63,8 | 1,42 |
| gfs_seamless | 73,3 | 1,54 |
| icon_eu | **77,1** | **1,07** |
| icon_seamless | **77,1** | **1,07** |
| meteofrance_seamless | 68,8 | 1,54 |
| meteoswiss_icon_seamless | 75,5 | 1,23 |
| ukmo_seamless | 70,2 | 1,47 |

Cas notés : Ciel /100 58 ; Température, erreur °C 58.

## Demi-journées J+4 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | 73,5 | 1,30 |
| ecmwf_aifs025_single | 66,9 | 1,71 |
| ecmwf_ifs025 | **76,7** | 1,49 |
| gem_seamless | 62,2 | 1,32 |
| gfs_seamless | 71,6 | 1,60 |
| icon_eu | 70,0 | 1,37 |
| icon_seamless | 70,0 | 1,37 |
| meteoswiss_icon_seamless | 68,0 | **1,25** |
| ukmo_seamless | 68,0 | 1,81 |

Cas notés : Ciel /100 55 ; Température, erreur °C 55.
Écartés faute de données sur la période (au moins une variable) : meteofrance_seamless.

## Demi-journées J+5 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | 58,9 | 1,84 |
| ecmwf_aifs025_single | 64,4 | 1,79 |
| ecmwf_ifs025 | 62,0 | **1,69** |
| gem_seamless | 54,4 | 2,01 |
| gfs_seamless | 63,7 | 2,27 |
| icon_seamless | **69,6** | 1,75 |
| ukmo_seamless | 51,9 | 2,06 |

Cas notés : Ciel /100 54 ; Température, erreur °C 54.
Écartés faute de données sur la période (au moins une variable) : icon_eu, meteofrance_seamless, meteoswiss_icon_seamless.

## Demi-journées J+6 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | **63,1** | 1,86 |
| ecmwf_aifs025_single | 54,4 | **1,68** |
| ecmwf_ifs025 | 56,3 | 1,98 |
| gem_seamless | 57,7 | 2,42 |
| gfs_seamless | 53,7 | 2,95 |
| icon_seamless | 55,0 | 2,22 |
| ukmo_seamless | 57,1 | 2,08 |

Cas notés : Ciel /100 52 ; Température, erreur °C 52.
Écartés faute de données sur la période (au moins une variable) : icon_eu, meteofrance_seamless, meteoswiss_icon_seamless.

## Demi-journées J+7 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | 53,0 | **1,65** |
| ecmwf_aifs025_single | 47,2 | 1,71 |
| ecmwf_ifs025 | **56,0** | 1,98 |
| gem_seamless | 47,0 | 2,75 |
| gfs_seamless | 45,8 | 2,95 |

Cas notés : Ciel /100 50 ; Température, erreur °C 50.
Écartés faute de données sur la période (au moins une variable) : icon_eu, icon_seamless, meteofrance_seamless, meteoswiss_icon_seamless, ukmo_seamless.

## Pluie dans les 2 heures (tranches de 20 min) : toutes les sources

| Source | Pluie, réussite % |
|---|---|
| GRESIL | **54,8** |
| dmi_harmonie_arome_europe | 42,6 |
| ecmwf_ifs025 | 30,2 |
| icon_d2 | 45,6 |
| knmi_harmonie_arome_europe | 42,7 |
| meteofrance_arome_france | 46,9 |
| meteofrance_seamless | 43,6 |
| meteoswiss_icon_ch1 | 47,2 |
| meteoswiss_icon_ch2 | 46,1 |

Cas notés : Pluie, réussite % 4488.

