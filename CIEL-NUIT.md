# Ciel la nuit : quelle vérité terrain ?

Test du 10/10/2026 (`ciel_nuit.py`). La nuit, GRESIL n'annonce pas l'état du ciel : il a appris le ciel contre le soleil mesuré par satellite, qui n'existe pas la nuit. Pour apprendre le ciel de nuit, il faudrait une mesure des nuages jour et nuit qui représente Grenoble. On a vérifié, de jour, si deux candidates disent la même chose que le satellite.

8 760 heures de jour sèches (02/2024 → 10/2026), seuils réglés sur les mois impairs, mesurés sur les mois pairs.

| Source | Accord pondéré /100 | Catégorie exacte |
|---|---|---|
| METAR de l'aéroport Grenoble-Isère (LFLS, 40 km) | 82,5 | 71 % |
| Nébulosité « satellite » d'Open-Meteo (non documentée) | 80,9 | 69 % |
| Prévision Météo-France de la veille (nébulosité brute) | 64,6 | 53 % |
| Toujours « soleil » | 80,7 | 70 % |

Aucune des deux ne fait mieux que dire « soleil » à chaque heure.

- L'aéroport est automatique et code « CAVOK » 56 % du temps : pas de nuage sous ~1 500 m, rien sur les nuages plus hauts. Quand le satellite voit un ciel mitigé à Grenoble, l'aéroport annonce « dégagé » 56 % du temps.
- La nébulosité du satellite d'Open-Meteo est remplie jour et nuit mais ne suit pas le soleil mesuré : elle n'est pas une mesure exploitable ici.

**Conclusion** : pas de modèle de ciel de nuit avec ces sources. Seule piste restante : le masque nuageux EUMETSAT (infrarouge, jour et nuit, pixel de ~4 km, archive depuis 2004), via le Data Store EUMETSAT (compte gratuit à créer, ~23 000 fichiers horaires à découper autour de Grenoble).
