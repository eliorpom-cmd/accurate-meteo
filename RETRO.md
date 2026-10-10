# Nos prévisions rétroactives

Chaque mois prévu par un modèle entraîné sur tous les autres mois (recettes de `figer.py`). Fichiers dans `retro/`, une ligne par cas.

| Échéance | Mesure | Mega-modèle (rétroactif) | Cas |
|---|---|---|---|
| veille, heure par heure | condition /100 | 85.3 | 10085 |
| veille, heure par heure | réussite pluie % | 43.6 | 23489 |
| veille, heure par heure | erreur temperature | 1.01 | 23526 |
| veille, heure par heure | erreur vent | 0.64 | 23511 |
| veille, heure par heure | erreur rafales | 1.60 | 23514 |
| J+1, matin / après-midi | condition /100 | 88.4 | 1954 |
| J+1, matin / après-midi | erreur temperature | 0.84 | 1956 |
| J+1, matin / après-midi | erreur rafales | 1.50 | 1956 |
| J+2, matin / après-midi | condition /100 | 85.6 | 1954 |
| J+2, matin / après-midi | erreur temperature | 1.05 | 1956 |
| J+2, matin / après-midi | erreur rafales | 1.67 | 1956 |
| J+3, matin / après-midi | condition /100 | 83.0 | 1954 |
| J+3, matin / après-midi | erreur temperature | 1.16 | 1956 |
| J+3, matin / après-midi | erreur rafales | 1.77 | 1956 |
| J+4, matin / après-midi | condition /100 | 80.3 | 1954 |
| J+4, matin / après-midi | erreur temperature | 1.33 | 1956 |
| J+4, matin / après-midi | erreur rafales | 1.86 | 1956 |
| J+5, matin / après-midi | condition /100 | 76.3 | 1940 |
| J+5, matin / après-midi | erreur temperature | 1.48 | 1942 |
| J+5, matin / après-midi | erreur rafales | 1.98 | 1942 |
| J+6, matin / après-midi | condition /100 | 74.2 | 1938 |
| J+6, matin / après-midi | erreur temperature | 1.77 | 1940 |
| J+6, matin / après-midi | erreur rafales | 2.12 | 1940 |
| J+7, matin / après-midi | condition /100 | 76.9 | 1165 |
| J+7, matin / après-midi | erreur temperature | 1.94 | 1168 |
| J+7, matin / après-midi | erreur rafales | 2.07 | 1167 |
| 2 h, tranches de 20 min | réussite pluie % | 51.9 | 70319 |
