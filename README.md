# Campagne
des outils plus ou moins vibe codé pour s'installer à la campagne

Accessible à : [https://cremesalade.github.io/campagne/](https://cremesalade.github.io/campagne/)

## Structure
- `index.html` : page principale
- `results.html` : page de partage (paramètres encodés en base64 URL)
- `static/` : JS/CSS
- `data/` : CSV source + JSON générés
- `scripts/build_data.py` : conversion CSV -> JSON + index
- `scripts/test_static.py` : tests rapides (données + logique)
- `serve.py` : serveur statique local

## Générer les données JSON
```bash
python scripts/build_data.py
```

## Tests rapides
```bash
python scripts/test_static.py
```

## Lancer en local
```bash
python serve.py
```
Puis ouvrir http://127.0.0.1:8000

## Déploiement GitHub Pages
- Assurez-vous que `index.html`, `results.html`, `static/` et `data/` sont à la racine du dépôt publié.
- Les liens sont relatifs, donc compatibles avec un sous-chemin (repo GitHub Pages).

## Tests interactifs
Lancer le serveur puis ouvrir http://127.0.0.1:8000/tests.html
Le bouton lance des sc?narios (autocomplete, recherche, partage).

## Selenium
- Lancer le serveur: python serve.py
- Lancer le test: python tests/selenium_smoke.py
(Chrome installe requis. Selenium Manager telecharge le driver si besoin.)

## Corriger les coordonnees manquantes
Script: scripts/fix_missing_coords.py
Usage: python scripts/fix_missing_coords.py
