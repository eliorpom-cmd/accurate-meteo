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

## Masque nuageux EUMETSAT (même jour)

Lu sur le serveur de cartes public d'EUMETSAT (`clm.py`, sans compte, archive depuis 2020) : 5 × 5 pixels autour de Grenoble à chaque mi-heure, nuage oui/non, plus la hauteur du sommet des nuages (codée en couleur, 63 % de l'archive téléchargée).

| Source (de jour, contre le soleil mesuré) | Accord /100 |
|---|---|
| Masque, seuils simples (pixel de Grenoble → 25 pixels) | 61 à 74 |
| Masque, petit modèle appris sur les 25 pixels + mois + heure | 84,2 |
| Masque + hauteur des nuages, modèle appris | 81,5 à 82,7 (sur 63 % des heures) |
| Toujours « soleil » | ~79 |
| **Prévision GRESIL du ciel, heure par heure** | **87,9** |

- Le masque dit « nuage » au-dessus de Grenoble 40 % du temps quand le soleil brille : il compte les voiles fins que la lumière traverse, et les nuages sur les massifs.
- La hauteur des nuages n'apporte rien de plus.
- Une « mesure » moins fiable de jour (84) que notre propre prévision (87,9) ne peut pas servir à l'entraîner la nuit, où elle serait en plus moins bonne (infrarouge seul).

**Conclusion** : pas de modèle de ciel de nuit. La nuit reste « nuit » (température, pluie, vent). Piste fermée le 10/10/2026 ; à rouvrir seulement si une station proche se met à mesurer la nébulosité (céilomètre ou caméra de ciel).
