# Documentation - Campagne

## Vue d'ensemble

**Campagne** est une application web qui aide les utilisateurs à trouver des communes rurales idéales en France selon des critères de recherche personnalisés. L'application combine des données démographiques, de prix immobiliers, climatiques, politiques et de services d'urgence pour permettre des décisions éclairées.

**Accès en ligne** : https://cremesalade.github.io/campagne/

---

## But du projet

Le projet répond à une question concrète : **"Où s'installer en France rurale ?"**

L'application permet de :
- Définir des **zones de recherche** autour de villes de référence
- Filtrer par **population** (min/max)
- Visualiser les résultats sur une **carte interactive**
- Consulter les **prix au m²** (appartements et maisons)
- Voir la **tendance politique** (vote extrême droite)
- Localiser les **services d'urgence** à proximité
- **Partager** les résultats via un lien ou exporter en CSV/JSON

---

## Structure du projet

```
campagne/
├── index.html                 # Interface de recherche principale
├── results.html              # Page d'affichage des résultats (partageable)
├── serve.py                  # Serveur Python local
│
├── static/                   # Assets frontend
│   ├── css/
│   │   └── app.css          # Styles (thème vert, 17KB)
│   └── js/
│       ├── app.js           # Contrôleur UI principal (1606 lignes)
│       ├── search-worker.js # Web Worker pour l'algorithme de recherche
│       ├── results-view.js  # Logique de la page résultats
│       └── logs.js          # Utilitaires de logging
│
├── data/                     # Fichiers de données JSON
│   ├── communes_enrichies.csv        # Données sources (7MB+)
│   ├── communes_enrichies.json       # Base de données complète (17MB)
│   ├── communes_index.json           # Index de recherche (4.8MB)
│   ├── urgences_service_public.json  # Services d'urgence
│   └── meta.json                     # Métadonnées du dataset
│
├── scripts/                  # Scripts Python de build
│   ├── build_data.py        # Convertisseur CSV → JSON
│   ├── test_static.py       # Tests d'intégration
│   └── fix_missing_coords.py # Utilitaire de nettoyage
│
├── Sociogramme/             # Bonus : Visualisation réseau social
│   ├── social_network_generator.py
│   ├── network_graph.html
│   └── relations.csv
│
├── tests/                   # Tests E2E & UI
│   ├── selenium_smoke.py
│   ├── selenium_e2e.py
│   └── *.png
│
└── docs/                    # Cette documentation
```

---

## Documentation détaillée

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | Architecture technique en 4 couches |
| [Moteur de recherche](./search-engine.md) | Algorithme de recherche et Web Worker |
| [Interface utilisateur](./ui.md) | Composants UI et interactions |
| [Données](./data.md) | Structure des données et scripts de build |

---

## Technologies utilisées

| Couche | Technologie | Usage |
|--------|-------------|-------|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) | UI & Interactivité |
| **Cartes** | Leaflet 1.9.4, OpenStreetMap | Visualisation géographique |
| **Backend** | Python 3.x | Traitement des données |
| **Données** | JSON, CSV | Stockage & Transfert |
| **Tests** | Selenium, Chrome WebDriver | Tests E2E |
| **Workers** | Web Workers API | Calculs parallèles |
| **Encodage** | Base64url | Compression paramètres URL |

---

## Lancement local

```bash
# Serveur Python simple
python serve.py

# Ou avec Python directement
python -m http.server 8000

# Ouvrir http://localhost:8000
```

---

## Flux de données simplifié

```
Entrée utilisateur (villes, rayon, population)
    ↓
Thread principal (app.js)
    ↓
Web Worker (search-worker.js)
    ├→ Charge communes_enrichies.json
    ├→ Applique filtres géographiques
    ├→ Calcule distances (Haversine)
    ├→ Trouve services d'urgence
    └→ Retourne top 500 résultats
    ↓
Thread principal
    ├→ Affiche tableau
    ├→ Met à jour carte Leaflet
    └→ Affiche urgences
    ↓
Export utilisateur
    ├→ CSV / JSON
    └→ Lien partageable (base64url)
```
