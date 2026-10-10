# Sous-modèle : pluie dans les 2 prochaines heures (tranches de 20 min)

Station GRENOBLE-CEA-RADOME. Une tranche est pluvieuse à partir de 0.05 mm. Test honnête : chaque mois de 2025-10-01 à 2026-10-08 est prédit par un modèle entraîné sur tous les autres mois (depuis 2024-02-01). Le seuil de décision est choisi sur les mois d'entraînement seulement.

26590 tranches testées, dont 7.1 % pluvieuses. Chaque tranche est notée 6 fois (prévision faite 0, 20, 40, 60, 80 et 100 min avant son début), toutes les prévisions sur exactement les mêmes lignes.

- Indice de réussite : tranches pluvieuses prévues et vues / tranches où il a plu ou été prévu de pleuvoir.
- Pluie vue : part des tranches pluvieuses annoncées.
- Fausses alertes : part des tranches annoncées pluvieuses restées sèches.
- Justes : part de toutes les tranches (sèches ou pluvieuses) bien prévues.

| Prévision | Indice de réussite | Pluie vue | Fausses alertes | Justes |
|---|---|---|---|---|
| **Sous-modèle 2 : + pluie observée** | 57.8 % | 72 % | 26 % | 96.3 % |
| **Sous-modèle 1 : modèles seuls** | 56.6 % | 72 % | 27 % | 96.1 % |
| icon_d2 | 50.9 % | 69 % | 34 % | 95.3 % |
| meteofrance_arome_france | 49.5 % | 66 % | 34 % | 95.2 % |
| AROME et ICON-D2 d'accord | 48.7 % | 54 % | 16 % | 96.0 % |
| meteoswiss_icon_ch1 | 48.2 % | 68 % | 37 % | 94.9 % |
| meteoswiss_icon_ch2 | 47.7 % | 69 % | 39 % | 94.7 % |
| meteofrance_seamless | 46.2 % | 57 % | 29 % | 95.3 % |
| Persistance (comme les 20 dernières min) | 44.7 % | 62 % | 38 % | 94.6 % |
| dmi_harmonie_arome_europe | 41.8 % | 69 % | 48 % | 93.3 % |
| knmi_harmonie_arome_europe | 40.0 % | 71 % | 52 % | 92.4 % |
| ecmwf_ifs025 | 38.2 % | 81 % | 58 % | 90.7 % |

Indice de réussite selon l'avance de la prévision :

| Avance | Sous-modèle 1 | Sous-modèle 2 | Persistance | AROME |
|---|---|---|---|---|
| 0 min | 56.6 % | 59.9 % | 58.8 % | 49.5 % |
| 20 min | 56.6 % | 58.1 % | 50.2 % | 49.5 % |
| 40 min | 56.6 % | 57.7 % | 44.9 % | 49.5 % |
| 60 min | 56.6 % | 56.8 % | 41.1 % | 49.5 % |
| 80 min | 56.6 % | 57.2 % | 38.9 % | 49.5 % |
| 100 min | 56.6 % | 57.2 % | 36.4 % | 49.5 % |

Seuils choisis : variante 1 de 0.37 à 0.40, variante 2 de 0.33 à 0.41. Durée du calcul : 5 min.

## Conclusions

- Le sous-modèle 1 (modèles seuls) passe l'indice de réussite de 50,9 % (ICON-D2, meilleur modèle seul) à 56,6 %. Il voit un peu plus de pluie (72 % contre 69 %) avec moins de fausses alertes (27 % contre 34 %).
- Ajouter la pluie observée (sous-modèle 2) n'apporte que 1,2 point en moyenne : +3,3 points à 0 min d'avance, presque rien au-delà de 40 min.
- La persistance est bonne à très court terme (58,8 % à 0 min) mais tombe à 36 % à 100 min. Le sous-modèle 2 reste au-dessus à toutes les avances.
- Le vote « AROME et ICON-D2 d'accord » réduit les fausses alertes (16 %) mais rate près de la moitié de la pluie.
- Le sous-modèle 2 demande les observations 6 minutes en direct (API publique Météo-France, clé gratuite). Il n'est utilisable que si on branche cette source ; sans elle, le sous-modèle 1 fait presque aussi bien.

Limite : l'archive Open-Meteo (Historical Forecast) assemble les premières heures de chaque run. En direct, le dernier run disponible a souvent 1 à 3 h de retard : les modèles (et donc les deux sous-modèles) seront un peu moins bons qu'ici, la persistance non.
