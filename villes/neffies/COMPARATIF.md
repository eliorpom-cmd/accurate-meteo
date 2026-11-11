# GRESIL en direct contre chaque modèle météo — Néffiès

Prévisions de GRESIL réellement publiées (journal de production, 496 enregistrements du 21/10/2026 17 h UTC au 11/11/2026 08 h UTC), comparées à ce que chaque modèle météo annonçait avec la même avance (Open-Meteo Previous Runs) et à la station PEZENAS-TOURBES (dernière mesure : 11/11/2026 04 h UTC ; ciel : satellite). Tous notés sur les mêmes cas. Rien n'est rejoué pour GRESIL.

## Résumé

« Meilleur modèle seul » = le meilleur des modèles sur cette ligne, choisi après coup (avantage aux modèles). Écart : positif = GRESIL meilleur ; entre crochets, intervalle à 90 % par tirage de jours entiers. « Bat » = nombre de modèles que GRESIL dépasse.

| Échéance | Variable | GRESIL | Meilleur modèle seul | Écart [90 %] | Bat | Cas | Verdict |
|---|---|---|---|---|---|---|---|
| Veille, heure par heure | Ciel /100 | 82,6 | 86,1 (icon_d2) | −3,5 [-8,2 ; 0,4] | 7/14 | 157 (19 j) | pas de différence sûre |
| Veille, heure par heure | Pluie, réussite % | 28,1 | 42,9 (meteofrance_seamless) | −14,7 [-27,9 ; 1,6] | 4/14 | 462 (21 j), 30 avec pluie | pas de différence sûre |
| Veille, heure par heure | Température, erreur °C | 1,22 | 1,08 (icon_d2) | −0,14 [-0,31 ; 0,02] | 4/14 | 462 (21 j) | pas de différence sûre |
| Veille, heure par heure | Vent, erreur m/s | 0,84 | 0,89 (icon_d2) | +0,05 [-0,03 ; 0,14] | 14/14 | 462 (21 j) | pas de différence sûre |
| Veille, heure par heure | Rafales, erreur m/s | 1,33 | 1,46 (meteofrance_seamless) | +0,13 [-0,03 ; 0,29] | 12/12 | 462 (21 j) | pas de différence sûre |
| Demi-journées J+1 | Ciel /100 | 93,4 | 89,5 (icon_eu) | +3,9 [-1,3 ; 9,2] | 9/9 | 38 (19 j) | pas de différence sûre |
| Demi-journées J+1 | Température, erreur °C | 0,82 | 0,87 (meteoswiss_icon_seamless) | +0,05 [-0,12 ; 0,21] | 9/9 | 38 (19 j) | pas de différence sûre |
| Demi-journées J+2 | Ciel /100 | 86,1 | 86,1 (ecmwf_ifs025) | +0,0 [-7,0 ; 6,9] | 8/9 | 36 (18 j) | pas de différence sûre |
| Demi-journées J+2 | Température, erreur °C | 0,82 | 0,79 (ukmo_seamless) | −0,03 [-0,28 ; 0,23] | 8/9 | 36 (18 j) | pas de différence sûre |
| Demi-journées J+3 | Ciel /100 | 88,2 | 82,4 (ecmwf_aifs025_single) | +5,9 [-5,9 ; 19,1] | 9/9 | 34 (17 j) | pas de différence sûre |
| Demi-journées J+3 | Température, erreur °C | 0,91 | 0,83 (ukmo_seamless) | −0,08 [-0,37 ; 0,20] | 8/9 | 34 (17 j) | pas de différence sûre |
| Demi-journées J+4 | Ciel /100 | 79,7 | 84,4 (ecmwf_aifs025_single) | −4,7 [-18,8 ; 7,8] | 7/8 | 32 (16 j) | pas de différence sûre |
| Demi-journées J+4 | Température, erreur °C | 1,12 | 0,89 (meteoswiss_icon_seamless) | −0,23 [-0,52 ; 0,08] | 5/8 | 32 (16 j) | pas de différence sûre |
| Demi-journées J+5 | Ciel /100 | 78,3 | 75,0 (ecmwf_aifs025_single) | +3,3 [-11,7 ; 16,7] | 6/6 | 30 (15 j) | pas de différence sûre |
| Demi-journées J+5 | Température, erreur °C | 1,24 | 0,99 (ecmwf_ifs025) | −0,25 [-0,74 ; 0,17] | 4/6 | 30 (15 j) | pas de différence sûre |
| Demi-journées J+6 | Ciel /100 | 83,9 | 67,9 (ecmwf_ifs025) | +16,1 [3,5 ; 32,1] | 6/6 | 28 (14 j) | GRESIL meilleur |
| Demi-journées J+6 | Température, erreur °C | 1,55 | 1,37 (ecmwf_ifs025) | −0,17 [-0,54 ; 0,23] | 3/6 | 28 (14 j) | pas de différence sûre |
| Demi-journées J+7 | Ciel /100 | 78,8 | 67,3 (ecmwf_aifs025_single) | +11,5 [-3,8 ; 28,8] | 4/4 | 26 (13 j) | pas de différence sûre |
| Demi-journées J+7 | Température, erreur °C | 1,57 | 1,53 (ecmwf_aifs025_single) | −0,04 [-0,25 ; 0,19] | 3/4 | 26 (13 j) | pas de différence sûre |
| 2 prochaines heures | Pluie, réussite % | 48,1 | 43,8 (meteofrance_arome_france) | +4,3 [-1,2 ; 12,5] | 8/8 | 2868 (22 j), 134 avec pluie | pas de différence sûre |

Ciel = soleil / mitigé / couvert / pluie, de jour seulement, crédit partiel entre catégories voisines. Réussite pluie = cas de pluie bien annoncés / (bien annoncés + manqués + fausses alertes) ; pluie = au moins 0.2 mm dans l'heure, 0.05 mm par tranche de 20 min.

## Contre quatre modèles connus, un par un

Météo-France (meteofrance_seamless), ECMWF IFS (européen), ICON (allemand, icon_seamless), GFS (américain). Mêmes cas que le résumé, même lecture de l'écart.

| Échéance | Variable | Modèle | GRESIL | Modèle | Écart [90 %] | Verdict |
|---|---|---|---|---|---|---|
| Veille, heure par heure | Ciel /100 | meteofrance_seamless | 82,6 | 81,7 | +0,9 [-7,3 ; 6,8] | pas de différence sûre |
| Veille, heure par heure | Ciel /100 | ecmwf_ifs025 | 82,6 | 82,2 | +0,4 [-7,9 ; 8,1] | pas de différence sûre |
| Veille, heure par heure | Ciel /100 | icon_seamless | 82,6 | 86,1 | −3,5 [-8,2 ; 0,4] | pas de différence sûre |
| Veille, heure par heure | Ciel /100 | gfs_seamless | 82,6 | 78,7 | +3,9 [-6,1 ; 12,9] | pas de différence sûre |
| Veille, heure par heure | Pluie, réussite % | meteofrance_seamless | 28,1 | 42,9 | −14,7 [-27,9 ; 1,6] | pas de différence sûre |
| Veille, heure par heure | Pluie, réussite % | ecmwf_ifs025 | 28,1 | 32,5 | −4,3 [-24,7 ; 13,1] | pas de différence sûre |
| Veille, heure par heure | Pluie, réussite % | icon_seamless | 28,1 | 31,2 | −3,1 [-19,5 ; 9,8] | pas de différence sûre |
| Veille, heure par heure | Pluie, réussite % | gfs_seamless | 28,1 | 32,0 | −3,9 [-27,7 ; 13,8] | pas de différence sûre |
| Veille, heure par heure | Température, erreur °C | meteofrance_seamless | 1,22 | 1,16 | −0,06 [-0,20 ; 0,07] | pas de différence sûre |
| Veille, heure par heure | Température, erreur °C | ecmwf_ifs025 | 1,22 | 1,13 | −0,09 [-0,30 ; 0,10] | pas de différence sûre |
| Veille, heure par heure | Température, erreur °C | icon_seamless | 1,22 | 1,08 | −0,14 [-0,31 ; 0,02] | pas de différence sûre |
| Veille, heure par heure | Température, erreur °C | gfs_seamless | 1,22 | 1,35 | +0,13 [-0,02 ; 0,28] | pas de différence sûre |
| Veille, heure par heure | Vent, erreur m/s | meteofrance_seamless | 0,84 | 1,05 | +0,21 [0,12 ; 0,30] | GRESIL meilleur |
| Veille, heure par heure | Vent, erreur m/s | ecmwf_ifs025 | 0,84 | 1,27 | +0,44 [0,29 ; 0,60] | GRESIL meilleur |
| Veille, heure par heure | Vent, erreur m/s | icon_seamless | 0,84 | 0,89 | +0,05 [-0,03 ; 0,14] | pas de différence sûre |
| Veille, heure par heure | Vent, erreur m/s | gfs_seamless | 0,84 | 1,72 | +0,89 [0,65 ; 1,19] | GRESIL meilleur |
| Veille, heure par heure | Rafales, erreur m/s | meteofrance_seamless | 1,33 | 1,46 | +0,13 [-0,03 ; 0,29] | pas de différence sûre |
| Veille, heure par heure | Rafales, erreur m/s | icon_seamless | 1,33 | 1,88 | +0,55 [0,29 ; 0,82] | GRESIL meilleur |
| Veille, heure par heure | Rafales, erreur m/s | gfs_seamless | 1,33 | 2,26 | +0,93 [0,68 ; 1,19] | GRESIL meilleur |
| Demi-journées J+1 | Ciel /100 | meteofrance_seamless | 93,4 | 82,9 | +10,5 [3,9 ; 18,4] | GRESIL meilleur |
| Demi-journées J+1 | Ciel /100 | ecmwf_ifs025 | 93,4 | 84,2 | +9,2 [1,3 ; 18,4] | GRESIL meilleur |
| Demi-journées J+1 | Ciel /100 | icon_seamless | 93,4 | 88,2 | +5,3 [1,3 ; 10,5] | GRESIL meilleur |
| Demi-journées J+1 | Ciel /100 | gfs_seamless | 93,4 | 77,6 | +15,8 [6,6 ; 26,3] | GRESIL meilleur |
| Demi-journées J+1 | Température, erreur °C | meteofrance_seamless | 0,82 | 1,06 | +0,24 [-0,03 ; 0,51] | pas de différence sûre |
| Demi-journées J+1 | Température, erreur °C | ecmwf_ifs025 | 0,82 | 1,00 | +0,18 [-0,11 ; 0,46] | pas de différence sûre |
| Demi-journées J+1 | Température, erreur °C | icon_seamless | 0,82 | 0,99 | +0,17 [-0,06 ; 0,42] | pas de différence sûre |
| Demi-journées J+1 | Température, erreur °C | gfs_seamless | 0,82 | 1,15 | +0,33 [0,08 ; 0,60] | GRESIL meilleur |
| Demi-journées J+3 | Ciel /100 | meteofrance_seamless | 88,2 | 79,4 | +8,8 [-2,9 ; 22,1] | pas de différence sûre |
| Demi-journées J+3 | Ciel /100 | ecmwf_ifs025 | 88,2 | 75,0 | +13,2 [0,0 ; 27,9] | pas de différence sûre |
| Demi-journées J+3 | Ciel /100 | icon_seamless | 88,2 | 76,5 | +11,8 [1,5 ; 23,5] | GRESIL meilleur |
| Demi-journées J+3 | Ciel /100 | gfs_seamless | 88,2 | 70,0 | +18,2 [5,9 ; 31,5] | GRESIL meilleur |
| Demi-journées J+3 | Température, erreur °C | meteofrance_seamless | 0,91 | 1,34 | +0,43 [0,01 ; 0,89] | GRESIL meilleur |
| Demi-journées J+3 | Température, erreur °C | ecmwf_ifs025 | 0,91 | 0,93 | +0,02 [-0,27 ; 0,30] | pas de différence sûre |
| Demi-journées J+3 | Température, erreur °C | icon_seamless | 0,91 | 1,09 | +0,17 [-0,15 ; 0,50] | pas de différence sûre |
| Demi-journées J+3 | Température, erreur °C | gfs_seamless | 0,91 | 1,27 | +0,36 [0,06 ; 0,64] | GRESIL meilleur |
| Demi-journées J+5 | Ciel /100 | ecmwf_ifs025 | 78,3 | 70,0 | +8,3 [-8,3 ; 23,3] | pas de différence sûre |
| Demi-journées J+5 | Ciel /100 | icon_seamless | 78,3 | 61,7 | +16,7 [3,3 ; 28,3] | GRESIL meilleur |
| Demi-journées J+5 | Ciel /100 | gfs_seamless | 78,3 | 73,3 | +5,0 [-11,7 ; 20,0] | pas de différence sûre |
| Demi-journées J+5 | Température, erreur °C | ecmwf_ifs025 | 1,24 | 0,99 | −0,25 [-0,74 ; 0,17] | pas de différence sûre |
| Demi-journées J+5 | Température, erreur °C | icon_seamless | 1,24 | 1,22 | −0,02 [-0,52 ; 0,40] | pas de différence sûre |
| Demi-journées J+5 | Température, erreur °C | gfs_seamless | 1,24 | 1,53 | +0,29 [-0,21 ; 0,76] | pas de différence sûre |
| Demi-journées J+7 | Ciel /100 | ecmwf_ifs025 | 78,8 | 55,8 | +23,1 [7,7 ; 38,5] | GRESIL meilleur |
| Demi-journées J+7 | Ciel /100 | gfs_seamless | 78,8 | 63,5 | +15,4 [0,0 ; 28,8] | pas de différence sûre |
| Demi-journées J+7 | Température, erreur °C | ecmwf_ifs025 | 1,57 | 1,74 | +0,17 [-0,22 ; 0,54] | pas de différence sûre |
| Demi-journées J+7 | Température, erreur °C | gfs_seamless | 1,57 | 1,89 | +0,32 [-0,10 ; 0,81] | pas de différence sûre |
| 2 prochaines heures | Pluie, réussite % | meteofrance_seamless | 48,1 | 38,6 | +9,4 [0,0 ; 16,8] | pas de différence sûre |
| 2 prochaines heures | Pluie, réussite % | ecmwf_ifs025 | 48,1 | 25,6 | +22,5 [0,0 ; 32,4] | pas de différence sûre |
| 2 prochaines heures | Pluie, réussite % | meteofrance_arome_france | 48,1 | 43,8 | +4,3 [-1,2 ; 12,5] | pas de différence sûre |
| 2 prochaines heures | Pluie, réussite % | icon_d2 | 48,1 | 21,6 | +26,5 [0,0 ; 43,1] | pas de différence sûre |

## Veille pour le lendemain, heure par heure : tous les modèles

| Source | Ciel /100 | Pluie, réussite % | Température, erreur °C | Vent, erreur m/s | Rafales, erreur m/s |
|---|---|---|---|---|---|
| GRESIL | 82,6 | 28,1 | 1,22 | **0,84** | **1,33** |
| ecmwf_aifs025_single | 83,2 | 25,0 | 1,33 | 1,39 | - |
| ecmwf_ifs025 | 82,2 | 32,5 | 1,13 | 1,27 | - |
| gem_seamless | 77,0 | 28,1 | 1,35 | 1,29 | 2,04 |
| gfs_seamless | 78,7 | 32,0 | 1,35 | 1,72 | 2,26 |
| icon_d2 | **86,1** | 31,2 | **1,08** | 0,89 | 1,88 |
| icon_eu | 84,9 | 38,3 | 1,09 | 0,91 | 1,74 |
| icon_seamless | **86,1** | 31,2 | **1,08** | 0,89 | 1,88 |
| knmi_harmonie_arome_europe | 74,8 | 32,5 | 1,20 | 1,09 | 1,56 |
| meteofrance_arome_france | 81,7 | 40,5 | 1,16 | 1,06 | 1,50 |
| meteofrance_arpege_europe | 81,1 | 36,8 | 1,36 | 1,42 | 1,82 |
| meteofrance_seamless | 81,7 | **42,9** | 1,16 | 1,05 | 1,46 |
| meteoswiss_icon_ch2 | 83,2 | 25,8 | 1,20 | 0,94 | 1,55 |
| meteoswiss_icon_seamless | 83,2 | 25,8 | 1,20 | 0,94 | 1,55 |
| ukmo_seamless | 83,1 | 32,3 | 1,20 | 1,07 | 1,78 |

Cas notés : Ciel /100 157 ; Pluie, réussite % 462 ; Température, erreur °C 462 ; Vent, erreur m/s 462 ; Rafales, erreur m/s 462.
Écartés faute de données sur la période (au moins une variable) : ecmwf_aifs025_single, ecmwf_ifs025.

## Demi-journées J+1 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | **93,4** | **0,82** |
| ecmwf_aifs025_single | 80,3 | 1,12 |
| ecmwf_ifs025 | 84,2 | 1,00 |
| gem_seamless | 73,7 | 1,44 |
| gfs_seamless | 77,6 | 1,15 |
| icon_eu | 89,5 | 1,01 |
| icon_seamless | 88,2 | 0,99 |
| meteofrance_seamless | 82,9 | 1,06 |
| meteoswiss_icon_seamless | 88,9 | 0,87 |
| ukmo_seamless | 89,5 | 0,87 |

Cas notés : Ciel /100 38 ; Température, erreur °C 38.

## Demi-journées J+2 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | **86,1** | 0,82 |
| ecmwf_aifs025_single | 83,3 | 1,21 |
| ecmwf_ifs025 | **86,1** | 1,01 |
| gem_seamless | 73,6 | 1,49 |
| gfs_seamless | 72,2 | 1,16 |
| icon_eu | 76,4 | 0,97 |
| icon_seamless | 76,4 | 0,97 |
| meteofrance_seamless | 81,9 | 1,34 |
| meteoswiss_icon_seamless | 84,2 | 0,94 |
| ukmo_seamless | 75,0 | **0,79** |

Cas notés : Ciel /100 36 ; Température, erreur °C 36.

## Demi-journées J+3 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | **88,2** | 0,91 |
| ecmwf_aifs025_single | 82,4 | 1,32 |
| ecmwf_ifs025 | 75,0 | 0,93 |
| gem_seamless | 72,9 | 1,56 |
| gfs_seamless | 70,0 | 1,27 |
| icon_eu | 76,5 | 1,09 |
| icon_seamless | 76,5 | 1,09 |
| meteofrance_seamless | 79,4 | 1,34 |
| meteoswiss_icon_seamless | 76,5 | 1,14 |
| ukmo_seamless | 76,5 | **0,83** |

Cas notés : Ciel /100 34 ; Température, erreur °C 34.

## Demi-journées J+4 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | 79,7 | 1,12 |
| ecmwf_aifs025_single | **84,4** | 1,34 |
| ecmwf_ifs025 | 62,5 | 1,01 |
| gem_seamless | 70,3 | 1,65 |
| gfs_seamless | 67,2 | 1,53 |
| icon_eu | 70,3 | 1,16 |
| icon_seamless | 70,3 | 1,16 |
| meteoswiss_icon_seamless | 77,5 | **0,89** |
| ukmo_seamless | 64,1 | 1,11 |

Cas notés : Ciel /100 32 ; Température, erreur °C 32.
Écartés faute de données sur la période (au moins une variable) : meteofrance_seamless.

## Demi-journées J+5 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | **78,3** | 1,24 |
| ecmwf_aifs025_single | 75,0 | 1,26 |
| ecmwf_ifs025 | 70,0 | **0,99** |
| gem_seamless | 61,7 | 1,73 |
| gfs_seamless | 73,3 | 1,53 |
| icon_seamless | 61,7 | 1,22 |
| ukmo_seamless | 62,7 | 1,67 |

Cas notés : Ciel /100 30 ; Température, erreur °C 30.
Écartés faute de données sur la période (au moins une variable) : icon_eu, meteofrance_seamless, meteoswiss_icon_seamless.

## Demi-journées J+6 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | **83,9** | 1,55 |
| ecmwf_aifs025_single | 66,1 | 1,38 |
| ecmwf_ifs025 | 67,9 | **1,37** |
| gem_seamless | 62,5 | 1,80 |
| gfs_seamless | 67,1 | 2,04 |
| icon_seamless | 64,3 | 1,47 |
| ukmo_seamless | 57,1 | 1,62 |

Cas notés : Ciel /100 28 ; Température, erreur °C 28.
Écartés faute de données sur la période (au moins une variable) : icon_eu, meteofrance_seamless, meteoswiss_icon_seamless.

## Demi-journées J+7 : tous les modèles

| Source | Ciel /100 | Température, erreur °C |
|---|---|---|
| GRESIL | **78,8** | 1,57 |
| ecmwf_aifs025_single | 67,3 | **1,53** |
| ecmwf_ifs025 | 55,8 | 1,74 |
| gem_seamless | 67,3 | 1,68 |
| gfs_seamless | 63,5 | 1,89 |

Cas notés : Ciel /100 26 ; Température, erreur °C 26.
Écartés faute de données sur la période (au moins une variable) : icon_eu, icon_seamless, meteofrance_seamless, meteoswiss_icon_seamless, ukmo_seamless.

## Pluie dans les 2 heures (tranches de 20 min) : toutes les sources

| Source | Pluie, réussite % |
|---|---|
| GRESIL | **48,1** |
| dmi_harmonie_arome_europe | 32,2 |
| ecmwf_ifs025 | 25,6 |
| icon_d2 | 21,6 |
| knmi_harmonie_arome_europe | 38,6 |
| meteofrance_arome_france | 43,8 |
| meteofrance_seamless | 38,6 |
| meteoswiss_icon_ch1 | 37,3 |
| meteoswiss_icon_ch2 | 31,8 |

Cas notés : Pluie, réussite % 2868.

