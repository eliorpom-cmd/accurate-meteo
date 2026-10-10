# Fiabilité des modèles météo à Grenoble

Période 2024-02-01 → 2026-10-08. Vérité terrain : station GRENOBLE-CEA-RADOME (température, humidité, vent, pluie), GRENOBLE-LVD (pression), satellite EUMETSAT (soleil). Heures de jour seulement pour la condition.

Score /100 = condition 60 %, pluie_mm 10 %, vent 5 %, rafales 5 %, direction 5 %, temperature 7 %, humidite 4 %, pression 4 %. Condition : bonne catégorie = 1 point, voisine (soleil↔mitigé, mitigé↔couvert) = 0,5, couvert↔pluie = 0,3. Les autres paramètres : 100 × (1 − erreur moyenne / tolérance), tolérances heure : pluie_mm 2, vent 3, rafales 6, direction 90, temperature 3, humidite 20, pression 4.

Répartition observée des heures de jour : soleil 62 %, mitigé 21 %, couvert 9 %, pluie 8 %.

Colonnes « vu » : part des heures (ou créneaux) observés dans cette condition que le modèle avait prévus exactement. Colonnes mm, m/s, °… : erreur moyenne.

## 1. Tendance à 7 jours, matin et après-midi

Score /100 de chaque modèle selon le nombre de jours d'avance (60 % = condition générale du créneau). À chaque échéance, tous les modèles sont notés sur les mêmes créneaux.

| Modèle | J+1 | J+2 | J+3 | J+4 | J+5 | J+6 | J+7 |
|---|---|---|---|---|---|---|---|
| ecmwf_ifs025 | 75.1 | 73.7 | **72.5** | **69.2** | **65.3** | **59.3** | **58.0** |
| ecmwf_aifs025_single | 67.5 | 66.5 | 65.6 | 63.9 | 60.0 | 57.8 | 55.5 |
| icon_seamless | 75.6 | 73.6 | 71.8 | 67.2 | 59.9 | 55.8 | - |
| icon_eu | 76.1 | 73.6 | 71.8 | 67.2 | - | - | - |
| meteoswiss_icon_seamless | 75.3 | 72.7 | 71.9 | 68.0 | - | - | - |
| gfs_seamless | 71.3 | 68.9 | 67.2 | 62.4 | 59.8 | 58.1 | 55.2 |
| gem_seamless | 71.7 | 69.7 | 67.4 | 65.5 | 60.5 | 57.9 | 52.9 |
| ukmo_seamless | 73.3 | 66.9 | 66.2 | 61.7 | 58.1 | 55.9 | - |
| meteofrance_seamless | **76.8** | **73.7** | 70.4 | - | - | - | - |

- J+1 : période commune 2025-07-04 → 2026-10-08
- J+2 : période commune 2025-07-20 → 2026-10-08
- J+3 : période commune 2025-07-06 → 2026-10-08
- J+4 : période commune 2025-07-07 → 2026-10-08
- J+5 : période commune 2025-02-22 → 2026-10-08
- J+6 : période commune 2025-02-23 → 2026-10-08
- J+7 : période commune 2025-02-24 → 2026-10-08

Détail à J+1, J+3 et J+5 :

### J+1

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | meteofrance_seamless | **76.8** | 85.0 | 77% | 92% | 15% | 79% | 2.1 mm | 1.3 m/s | 2.0 m/s | - | 1.2°C | 7.6 % | 0.7 hPa |
| 2 | icon_eu | **76.1** | 84.6 | 76% | 84% | 20% | 83% | 2.0 mm | 0.7 m/s | 2.7 m/s | 38.0° | 1.3°C | 6.9 % | 1.0 hPa |
| 3 | icon_seamless | **75.6** | 86.3 | 78% | 90% | 22% | 80% | 3.2 mm | 1.3 m/s | 2.2 m/s | 23.1° | 1.1°C | 6.3 % | 0.8 hPa |
| 4 | meteoswiss_icon_seamless | **75.3** | 84.4 | 77% | 92% | 22% | 68% | 2.2 mm | 1.5 m/s | 2.6 m/s | 23.6° | 1.2°C | 7.6 % | 0.8 hPa |
| 5 | ecmwf_ifs025 | **75.1** | 84.5 | 80% | 90% | 30% | 91% | 2.2 mm | 1.0 m/s | - | 45.5° | 1.4°C | 8.0 % | 1.1 hPa |
| 6 | ukmo_seamless | **73.3** | 82.5 | 74% | 86% | 15% | 83% | 2.4 mm | 0.9 m/s | 2.8 m/s | 43.3° | 1.2°C | 6.8 % | 1.0 hPa |
| 7 | gem_seamless | **71.7** | 83.3 | 76% | 89% | 0% | 91% | 1.9 mm | 1.2 m/s | 4.9 m/s | 36.0° | 1.6°C | 9.3 % | 0.9 hPa |
| 8 | gfs_seamless | **71.3** | 83.1 | 77% | 86% | 38% | 88% | 2.3 mm | 0.7 m/s | 5.4 m/s | 37.7° | 1.6°C | 8.8 % | 0.8 hPa |
| 9 | ecmwf_aifs025_single | **67.5** | 77.1 | 72% | 84% | 0% | 100% | 1.6 mm | 1.0 m/s | - | 48.5° | 2.8°C | 7.9 % | 1.7 hPa |

### J+3

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ecmwf_ifs025 | **72.5** | 82.6 | 77% | 87% | 18% | 94% | 2.5 mm | 1.0 m/s | - | 45.3° | 1.5°C | 8.6 % | 1.3 hPa |
| 2 | meteoswiss_icon_seamless | **71.9** | 82.8 | 74% | 88% | 28% | 62% | 2.9 mm | 1.5 m/s | 2.8 m/s | 24.8° | 1.3°C | 8.3 % | 1.0 hPa |
| 3 | icon_seamless | **71.8** | 81.5 | 71% | 80% | 20% | 79% | 2.7 mm | 0.7 m/s | 2.8 m/s | 41.5° | 1.4°C | 7.3 % | 1.3 hPa |
| 4 | icon_eu | **71.8** | 81.5 | 71% | 80% | 20% | 79% | 2.7 mm | 0.7 m/s | 2.8 m/s | 41.5° | 1.4°C | 7.3 % | 1.3 hPa |
| 5 | meteofrance_seamless | **70.4** | 80.5 | 73% | 91% | 0% | 69% | 3.0 mm | 0.7 m/s | 2.3 m/s | - | 1.7°C | 10.0 % | 1.4 hPa |
| 6 | gem_seamless | **67.4** | 79.5 | 72% | 87% | 3% | 77% | 2.4 mm | 1.2 m/s | 4.9 m/s | 36.7° | 1.7°C | 10.5 % | 1.3 hPa |
| 7 | gfs_seamless | **67.2** | 78.7 | 70% | 79% | 30% | 81% | 2.4 mm | 0.7 m/s | 5.4 m/s | 37.9° | 1.8°C | 9.7 % | 1.2 hPa |
| 8 | ukmo_seamless | **66.2** | 74.5 | 64% | 73% | 25% | 82% | 2.7 mm | 0.9 m/s | 3.0 m/s | 52.6° | 1.5°C | 7.8 % | 1.3 hPa |
| 9 | ecmwf_aifs025_single | **65.6** | 75.1 | 70% | 81% | 0% | 99% | 1.7 mm | 1.0 m/s | - | 46.6° | 2.9°C | 8.7 % | 1.8 hPa |

### J+5

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ecmwf_ifs025 | **65.3** | 74.6 | 67% | 79% | 21% | 74% | 2.6 mm | 1.0 m/s | - | 47.0° | 1.8°C | 10.1 % | 1.9 hPa |
| 2 | gem_seamless | **60.5** | 72.2 | 64% | 80% | 8% | 65% | 2.5 mm | 1.3 m/s | 4.9 m/s | 43.1° | 2.0°C | 12.0 % | 2.1 hPa |
| 3 | ecmwf_aifs025_single | **60.0** | 68.3 | 63% | 72% | 0% | 94% | 1.7 mm | 1.0 m/s | - | 49.5° | 3.0°C | 9.8 % | 2.2 hPa |
| 4 | icon_seamless | **59.9** | 69.4 | 59% | 67% | 24% | 62% | 2.7 mm | 0.8 m/s | 3.3 m/s | 53.9° | 2.1°C | 11.5 % | 2.2 hPa |
| 5 | gfs_seamless | **59.8** | 71.1 | 61% | 73% | 42% | 53% | 2.3 mm | 0.7 m/s | 5.6 m/s | 46.7° | 2.2°C | 11.8 % | 2.2 hPa |
| 6 | ukmo_seamless | **58.1** | 66.3 | 57% | 68% | 16% | 62% | 3.1 mm | 1.0 m/s | 3.2 m/s | 55.1° | 1.8°C | 9.7 % | 2.1 hPa |

## 2. La veille pour le lendemain, heure par heure

Tous les modèles notés sur les mêmes heures (période commune 2025-07-04 → 2026-10-08).

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | icon_eu | **73.2** | 82.1 | 72% | 82% | 29% | 62% | 0.8 mm | 0.8 m/s | 2.2 m/s | 46.9° | 1.4°C | 8.8 % | 1.0 hPa |
| 2 | ecmwf_ifs025 | **72.8** | 83.1 | 77% | 88% | 31% | 82% | 0.8 mm | 1.0 m/s | - | 55.1° | 1.7°C | 9.8 % | 1.1 hPa |
| 3 | meteofrance_arome_france | **72.6** | 82.2 | 73% | 91% | 20% | 56% | 1.0 mm | 1.1 m/s | 1.9 m/s | 33.8° | 1.5°C | 10.7 % | 0.8 hPa |
| 4 | meteofrance_seamless | **72.4** | 82.3 | 73% | 91% | 20% | 56% | 1.0 mm | 1.3 m/s | 1.9 m/s | 30.9° | 1.6°C | 9.9 % | 0.8 hPa |
| 5 | icon_d2 | **72.3** | 82.9 | 72% | 86% | 35% | 58% | 1.2 mm | 1.3 m/s | 2.1 m/s | 30.6° | 1.5°C | 8.8 % | 0.9 hPa |
| 6 | icon_seamless | **72.3** | 82.9 | 72% | 86% | 35% | 58% | 1.2 mm | 1.3 m/s | 2.1 m/s | 30.6° | 1.5°C | 8.8 % | 0.9 hPa |
| 7 | meteoswiss_icon_ch2 | **72.0** | 82.5 | 72% | 88% | 29% | 48% | 1.1 mm | 1.4 m/s | 2.3 m/s | 30.9° | 1.5°C | 9.6 % | 0.8 hPa |
| 8 | meteoswiss_icon_seamless | **72.0** | 82.5 | 72% | 88% | 29% | 48% | 1.1 mm | 1.4 m/s | 2.3 m/s | 30.9° | 1.5°C | 9.6 % | 0.8 hPa |
| 9 | gem_seamless | **71.3** | 81.2 | 72% | 88% | 12% | 74% | 0.7 mm | 1.1 m/s | 3.7 m/s | 37.7° | 1.6°C | 10.3 % | 0.9 hPa |
| 10 | meteofrance_arpege_europe | **70.3** | 81.6 | 73% | 90% | 13% | 72% | 0.9 mm | 1.0 m/s | 2.5 m/s | 61.7° | 1.7°C | 10.7 % | 1.2 hPa |
| 11 | ukmo_seamless | **69.5** | 78.7 | 68% | 83% | 26% | 68% | 0.9 mm | 1.0 m/s | 2.4 m/s | 58.7° | 1.5°C | 7.8 % | 1.1 hPa |
| 12 | knmi_harmonie_arome_europe | **69.4** | 82.0 | 72% | 91% | 32% | 56% | 1.0 mm | 1.6 m/s | 2.8 m/s | 40.2° | 1.8°C | 11.3 % | 1.1 hPa |
| 13 | gfs_seamless | **68.8** | 79.7 | 71% | 83% | 43% | 75% | 0.9 mm | 0.9 m/s | 3.8 m/s | 38.0° | 1.9°C | 11.6 % | 0.8 hPa |
| 14 | ecmwf_aifs025_single | **68.5** | 76.7 | 69% | 85% | 1% | 95% | 0.5 mm | 0.9 m/s | - | 48.9° | 2.6°C | 8.7 % | 1.6 hPa |

## 3. Les 2 prochaines heures

Condition = 50 % pluie par tranches de 20 min (indice de réussite) + 50 % ciel heure par heure (soleil / mitigé / couvert / pluie). Autres paramètres : premières heures de chaque run.

Tous les modèles notés sur les mêmes heures (période commune 2025-07-03 → 2026-10-08).

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | icon_d2 | **65.9** | 67.6 | 76% | 89% | 38% | 64% | 0.8 mm | 1.3 m/s | 1.9 m/s | 24.7° | 1.4°C | 8.8 % | 0.8 hPa |
| 2 | meteofrance_arome_france | **65.6** | 65.4 | 75% | 93% | 19% | 59% | 0.8 mm | 1.3 m/s | 2.0 m/s | 23.4° | 1.0°C | 7.3 % | 0.6 hPa |
| 3 | meteoswiss_icon_ch1 | **65.3** | 65.5 | 74% | 86% | 39% | 60% | 0.8 mm | 1.6 m/s | 1.9 m/s | 21.3° | 1.0°C | 7.2 % | 0.6 hPa |
| 4 | meteofrance_seamless | **65.2** | 63.7 | 74% | 95% | 11% | 51% | 0.9 mm | 1.0 m/s | 1.9 m/s | 18.9° | 1.1°C | 6.2 % | 0.6 hPa |
| 5 | meteoswiss_icon_ch2 | **64.0** | 65.7 | 75% | 89% | 36% | 58% | 0.9 mm | 1.5 m/s | 2.1 m/s | 24.0° | 1.2°C | 7.9 % | 0.7 hPa |
| 6 | ecmwf_ifs025 | **61.3** | 62.2 | 84% | 93% | 39% | 85% | 0.7 mm | 1.0 m/s | 2.1 m/s | 52.8° | 1.4°C | 8.6 % | 1.0 hPa |
| 7 | knmi_harmonie_arome_europe | **57.2** | 59.6 | 72% | 89% | 28% | 63% | 1.0 mm | 1.6 m/s | 2.6 m/s | 35.3° | 1.5°C | 11.0 % | 0.9 hPa |
| 8 | dmi_harmonie_arome_europe | **56.1** | 60.9 | 73% | 91% | 35% | 59% | 1.0 mm | 2.0 m/s | 2.8 m/s | 33.8° | 1.9°C | 13.2 % | 0.9 hPa |

Pluie par tranches de 20 min (indice de réussite = tranches pluvieuses prévues et vues, sur toutes les tranches où il a plu ou été prévu de pleuvoir) :

- icon_d2 : 49 %
- meteofrance_arome_france : 47 %
- meteoswiss_icon_ch1 : 47 %
- meteofrance_seamless : 44 %
- meteoswiss_icon_ch2 : 46 %
- ecmwf_ifs025 : 36 %
- knmi_harmonie_arome_europe : 38 %
- dmi_harmonie_arome_europe : 39 %
