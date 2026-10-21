# Fiabilité des modèles météo à Néffiès

Période 2025-04-01 → 2026-10-20. Vérité terrain : station PEZENAS-TOURBES (température, humidité, vent, pluie), station 34209002 (pression), satellite EUMETSAT (soleil). Heures de jour seulement pour la condition.

Score /100 = condition 60 %, pluie_mm 10 %, vent 5 %, rafales 5 %, direction 5 %, temperature 7 %, humidite 4 %, pression 4 %. Condition : bonne catégorie = 1 point, voisine (soleil↔mitigé, mitigé↔couvert) = 0,5, couvert↔pluie = 0,3. Les autres paramètres : 100 × (1 − erreur moyenne / tolérance), tolérances heure : pluie_mm 2, vent 3, rafales 6, direction 90, temperature 3, humidite 20, pression 4.

Répartition observée des heures de jour : soleil 73 %, mitigé 18 %, couvert 5 %, pluie 4 %.

Colonnes « vu » : part des heures (ou créneaux) observés dans cette condition que le modèle avait prévus exactement. Colonnes mm, m/s, °… : erreur moyenne.

## 1. Tendance à 7 jours, matin et après-midi

Score /100 de chaque modèle selon le nombre de jours d'avance (60 % = condition générale du créneau). À chaque échéance, tous les modèles sont notés sur les mêmes créneaux.

| Modèle | J+1 | J+2 | J+3 | J+4 | J+5 | J+6 | J+7 |
|---|---|---|---|---|---|---|---|
| ecmwf_ifs025 | 77.3 | **75.9** | **74.8** | **70.9** | **67.4** | 60.5 | 57.6 |
| ecmwf_aifs025_single | 72.7 | 71.8 | 70.9 | 68.8 | 66.3 | **64.7** | **60.9** |
| icon_seamless | **78.6** | 74.5 | 74.3 | 69.4 | 63.4 | 60.4 | - |
| icon_eu | 77.8 | 74.5 | 74.3 | 69.5 | - | - | - |
| meteoswiss_icon_seamless | 77.3 | 75.1 | 72.6 | 69.1 | - | - | - |
| gfs_seamless | 74.5 | 72.0 | 70.0 | 65.7 | 62.9 | 63.1 | 58.5 |
| gem_seamless | 73.0 | 72.1 | 69.5 | 66.5 | 63.0 | 58.7 | 57.2 |
| ukmo_seamless | 75.4 | 71.0 | 68.6 | 65.1 | 60.8 | 59.0 | - |
| meteofrance_seamless | 77.2 | 75.5 | 71.6 | - | - | - | - |

- J+1 : période commune 2025-07-04 → 2026-10-20
- J+2 : période commune 2025-07-20 → 2026-10-20
- J+3 : période commune 2025-07-06 → 2026-10-20
- J+4 : période commune 2025-07-07 → 2026-10-20
- J+5 : période commune 2025-04-01 → 2026-10-20
- J+6 : période commune 2025-04-01 → 2026-10-20
- J+7 : période commune 2025-04-01 → 2026-10-20

Détail à J+1, J+3 et J+5 :

### J+1

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | icon_seamless | **78.6** | 86.4 | 78% | 94% | 22% | 43% | 2.6 mm | 0.7 m/s | 2.1 m/s | 22.8° | 1.1°C | 4.5 % | 0.4 hPa |
| 2 | icon_eu | **77.8** | 83.8 | 76% | 87% | 19% | 79% | 2.3 mm | 0.7 m/s | 1.7 m/s | 22.8° | 1.2°C | 4.4 % | 0.4 hPa |
| 3 | ecmwf_ifs025 | **77.3** | 84.3 | 79% | 93% | 19% | 88% | 2.4 mm | 0.9 m/s | - | 24.1° | 1.2°C | 5.8 % | 0.4 hPa |
| 4 | meteoswiss_icon_seamless | **77.3** | 86.8 | 79% | 94% | 31% | 49% | 3.2 mm | 1.0 m/s | 1.8 m/s | 25.1° | 1.0°C | 5.9 % | 0.5 hPa |
| 5 | meteofrance_seamless | **77.2** | 86.0 | 78% | 92% | 44% | 62% | 3.3 mm | 0.7 m/s | 1.4 m/s | 25.3° | 1.1°C | 5.6 % | 0.5 hPa |
| 6 | ukmo_seamless | **75.4** | 81.2 | 72% | 85% | 16% | 85% | 2.7 mm | 0.7 m/s | 1.6 m/s | 23.5° | 1.2°C | 5.0 % | 0.4 hPa |
| 7 | gfs_seamless | **74.5** | 83.0 | 75% | 89% | 25% | 84% | 2.1 mm | 1.3 m/s | 2.6 m/s | 24.6° | 1.3°C | 7.2 % | 0.7 hPa |
| 8 | gem_seamless | **73.0** | 83.0 | 77% | 91% | 9% | 79% | 2.9 mm | 0.8 m/s | 3.1 m/s | 24.8° | 1.7°C | 6.1 % | 0.5 hPa |
| 9 | ecmwf_aifs025_single | **72.7** | 78.9 | 74% | 90% | 0% | 94% | 2.3 mm | 0.9 m/s | - | 23.9° | 1.8°C | 5.8 % | 0.6 hPa |

### J+3

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ecmwf_ifs025 | **74.8** | 82.0 | 76% | 90% | 16% | 78% | 2.4 mm | 1.1 m/s | - | 26.7° | 1.3°C | 6.6 % | 0.8 hPa |
| 2 | icon_seamless | **74.3** | 82.1 | 74% | 86% | 12% | 74% | 2.6 mm | 0.9 m/s | 2.0 m/s | 27.1° | 1.4°C | 5.6 % | 0.9 hPa |
| 3 | icon_eu | **74.3** | 82.1 | 74% | 86% | 12% | 74% | 2.6 mm | 0.9 m/s | 2.0 m/s | 27.1° | 1.4°C | 5.6 % | 0.9 hPa |
| 4 | meteoswiss_icon_seamless | **72.6** | 83.7 | 75% | 91% | 25% | 31% | 3.8 mm | 1.1 m/s | 2.0 m/s | 28.6° | 1.2°C | 7.1 % | 0.8 hPa |
| 5 | meteofrance_seamless | **71.6** | 80.6 | 72% | 86% | 12% | 63% | 3.0 mm | 0.8 m/s | 1.8 m/s | 30.3° | 1.5°C | 8.3 % | 1.1 hPa |
| 6 | ecmwf_aifs025_single | **70.9** | 77.6 | 72% | 89% | 0% | 96% | 2.3 mm | 1.0 m/s | - | 25.0° | 1.9°C | 6.4 % | 0.9 hPa |
| 7 | gfs_seamless | **70.0** | 81.2 | 73% | 90% | 19% | 74% | 2.9 mm | 1.5 m/s | 3.0 m/s | 29.7° | 1.5°C | 8.3 % | 1.2 hPa |
| 8 | gem_seamless | **69.5** | 80.0 | 72% | 89% | 9% | 72% | 2.8 mm | 0.9 m/s | 3.2 m/s | 29.6° | 2.0°C | 7.3 % | 0.9 hPa |
| 9 | ukmo_seamless | **68.6** | 74.8 | 65% | 80% | 22% | 69% | 3.1 mm | 0.9 m/s | 2.0 m/s | 27.6° | 1.3°C | 6.7 % | 0.9 hPa |

### J+5

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ecmwf_ifs025 | **67.4** | 77.2 | 69% | 84% | 6% | 66% | 2.9 mm | 1.3 m/s | - | 38.6° | 1.7°C | 8.4 % | 1.6 hPa |
| 2 | ecmwf_aifs025_single | **66.3** | 73.7 | 66% | 83% | 0% | 82% | 2.4 mm | 1.1 m/s | - | 31.3° | 2.1°C | 7.7 % | 1.5 hPa |
| 3 | icon_seamless | **63.4** | 75.5 | 66% | 78% | 12% | 62% | 3.8 mm | 1.1 m/s | 2.7 m/s | 41.3° | 1.8°C | 8.7 % | 1.8 hPa |
| 4 | gem_seamless | **63.0** | 75.3 | 67% | 86% | 0% | 51% | 3.0 mm | 1.2 m/s | 3.6 m/s | 40.3° | 2.2°C | 9.6 % | 1.9 hPa |
| 5 | gfs_seamless | **62.9** | 74.9 | 64% | 81% | 24% | 40% | 2.8 mm | 1.6 m/s | 3.5 m/s | 40.8° | 1.9°C | 10.0 % | 2.2 hPa |
| 6 | ukmo_seamless | **60.8** | 68.5 | 57% | 73% | 17% | 52% | 3.2 mm | 1.1 m/s | 2.6 m/s | 39.3° | 1.7°C | 9.1 % | 1.9 hPa |

## 2. La veille pour le lendemain, heure par heure

Tous les modèles notés sur les mêmes heures (période commune 2025-07-04 → 2026-10-20).

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ecmwf_ifs025 | **77.4** | 85.6 | 78% | 90% | 25% | 70% | 0.8 mm | 1.3 m/s | - | 24.1° | 1.5°C | 7.2 % | 0.5 hPa |
| 2 | icon_eu | **77.2** | 84.8 | 75% | 85% | 31% | 67% | 1.0 mm | 0.9 m/s | 1.7 m/s | 22.4° | 1.3°C | 5.7 % | 0.5 hPa |
| 3 | icon_seamless | **77.1** | 86.8 | 78% | 91% | 26% | 38% | 1.2 mm | 0.9 m/s | 1.8 m/s | 22.7° | 1.3°C | 5.8 % | 0.5 hPa |
| 4 | icon_d2 | **77.1** | 86.8 | 78% | 91% | 26% | 38% | 1.2 mm | 0.9 m/s | 1.8 m/s | 22.7° | 1.3°C | 5.8 % | 0.5 hPa |
| 5 | ecmwf_aifs025_single | **75.9** | 82.5 | 75% | 89% | 5% | 85% | 0.6 mm | 1.3 m/s | - | 25.6° | 1.7°C | 7.2 % | 0.6 hPa |
| 6 | meteoswiss_icon_ch2 | **75.6** | 86.4 | 77% | 91% | 36% | 29% | 1.4 mm | 1.1 m/s | 1.7 m/s | 24.3° | 1.2°C | 6.9 % | 0.5 hPa |
| 7 | meteoswiss_icon_seamless | **75.6** | 86.4 | 77% | 91% | 36% | 29% | 1.4 mm | 1.1 m/s | 1.7 m/s | 24.3° | 1.2°C | 6.9 % | 0.5 hPa |
| 8 | gem_seamless | **74.7** | 83.7 | 75% | 89% | 15% | 67% | 0.9 mm | 1.1 m/s | 2.3 m/s | 26.1° | 1.7°C | 7.1 % | 0.5 hPa |
| 9 | meteofrance_arpege_europe | **74.5** | 84.6 | 75% | 88% | 28% | 58% | 1.0 mm | 1.3 m/s | 1.6 m/s | 24.3° | 1.7°C | 8.4 % | 0.5 hPa |
| 10 | gfs_seamless | **74.0** | 83.5 | 75% | 90% | 38% | 62% | 0.8 mm | 1.6 m/s | 2.4 m/s | 25.2° | 1.5°C | 8.6 % | 0.7 hPa |
| 11 | meteofrance_seamless | **73.7** | 85.5 | 76% | 90% | 40% | 42% | 1.6 mm | 1.1 m/s | 1.5 m/s | 24.6° | 1.4°C | 7.5 % | 0.5 hPa |
| 12 | meteofrance_arome_france | **73.6** | 85.4 | 76% | 90% | 38% | 44% | 1.6 mm | 1.1 m/s | 1.6 m/s | 24.5° | 1.4°C | 7.6 % | 0.5 hPa |
| 13 | ukmo_seamless | **72.8** | 80.1 | 69% | 80% | 33% | 65% | 1.2 mm | 1.0 m/s | 1.7 m/s | 23.0° | 1.3°C | 6.3 % | 0.5 hPa |
| 14 | knmi_harmonie_arome_europe | **72.1** | 84.2 | 75% | 90% | 50% | 41% | 1.6 mm | 1.1 m/s | 1.8 m/s | 24.6° | 1.6°C | 7.1 % | 0.5 hPa |

## 3. Les 2 prochaines heures

Condition = 50 % pluie par tranches de 20 min (indice de réussite) + 50 % ciel heure par heure (soleil / mitigé / couvert / pluie). Autres paramètres : premières heures de chaque run.

Tous les modèles notés sur les mêmes heures (période commune 2025-07-03 → 2026-10-20).

| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | meteofrance_seamless | **66.0** | 63.5 | 77% | 93% | 27% | 55% | 1.2 mm | 0.8 m/s | 1.4 m/s | 12.5° | 0.8°C | 3.4 % | 0.4 hPa |
| 2 | meteofrance_arome_france | **63.6** | 61.9 | 78% | 93% | 32% | 56% | 1.2 mm | 1.0 m/s | 1.4 m/s | 17.6° | 1.0°C | 5.0 % | 0.4 hPa |
| 3 | icon_d2 | **62.2** | 60.5 | 80% | 93% | 30% | 40% | 1.2 mm | 0.9 m/s | 1.7 m/s | 20.0° | 1.2°C | 5.0 % | 0.3 hPa |
| 4 | meteoswiss_icon_ch1 | **61.2** | 60.9 | 78% | 89% | 48% | 46% | 1.4 mm | 1.1 m/s | 1.6 m/s | 19.7° | 1.1°C | 5.5 % | 0.4 hPa |
| 5 | meteoswiss_icon_ch2 | **61.1** | 60.2 | 78% | 89% | 49% | 35% | 1.4 mm | 1.1 m/s | 1.5 m/s | 19.8° | 1.1°C | 5.8 % | 0.3 hPa |
| 6 | ecmwf_ifs025 | **61.0** | 56.7 | 84% | 93% | 36% | 76% | 0.8 mm | 1.2 m/s | 1.6 m/s | 21.8° | 1.3°C | 6.1 % | 0.3 hPa |
| 7 | dmi_harmonie_arome_europe | **59.9** | 58.9 | 75% | 89% | 60% | 53% | 1.3 mm | 1.0 m/s | 1.6 m/s | 21.7° | 1.3°C | 6.5 % | 0.4 hPa |
| 8 | knmi_harmonie_arome_europe | **59.9** | 59.9 | 76% | 90% | 63% | 55% | 1.4 mm | 1.0 m/s | 1.8 m/s | 22.0° | 1.3°C | 6.3 % | 0.3 hPa |

Pluie par tranches de 20 min (indice de réussite = tranches pluvieuses prévues et vues, sur toutes les tranches où il a plu ou été prévu de pleuvoir) :

- meteofrance_seamless : 41 %
- meteofrance_arome_france : 37 %
- icon_d2 : 33 %
- meteoswiss_icon_ch1 : 35 %
- meteoswiss_icon_ch2 : 33 %
- ecmwf_ifs025 : 25 %
- dmi_harmonie_arome_europe : 33 %
- knmi_harmonie_arome_europe : 35 %
