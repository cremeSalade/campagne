# Architecture Technique

## Vue d'ensemble

L'application Campagne suit une architecture en **4 couches** distinctes :

```
┌─────────────────────────────────────────────────────────┐
│                    COUCHE PRÉSENTATION                   │
│              (index.html, results.html, CSS)            │
├─────────────────────────────────────────────────────────┤
│                    COUCHE APPLICATION                    │
│                (app.js, results-view.js)                │
├─────────────────────────────────────────────────────────┤
│                    COUCHE CALCUL                         │
│                  (search-worker.js)                      │
├─────────────────────────────────────────────────────────┤
│                    COUCHE DONNÉES                        │
│            (JSON files, build_data.py)                  │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Couche Données (Python Backend)

**Fichiers** : `scripts/build_data.py`, `data/*.json`

### Responsabilités
- Convertir les données CSV sources (7MB) en fichiers JSON optimisés
- Normaliser les noms de villes françaises (suppression accents, majuscules)
- Calculer les métadonnées (total communes, comptage urgences)
- Pré-traiter : codes postaux, populations, coordonnées, prix, températures, altitude

### Fonctions clés

```python
normalize_name()      # Normalisation NFD pour accents français
to_float() / to_int() # Conversion de type sécurisée
read_communes()       # Parsing CSV + génération index
read_urgences()       # Parsing services d'urgence
write_json()          # Sortie JSON optimisée
```

### Fichiers générés

| Fichier | Taille | Description |
|---------|--------|-------------|
| `communes_enrichies.json` | 17MB | 36k+ communes avec tous attributs |
| `communes_index.json` | 4.8MB | Index léger (nom, coords, population) |
| `urgences_service_public.json` | 300KB+ | Hôpitaux et urgences |
| `meta.json` | <1KB | Statistiques et métadonnées |

---

## 2. Couche Calcul (Web Worker)

**Fichier** : `static/js/search-worker.js` (308 lignes)

### Pourquoi un Web Worker ?

Les Web Workers permettent d'exécuter du JavaScript dans un thread séparé, ce qui :
- **Évite le blocage de l'UI** pendant les calculs lourds
- Permet de traiter 36 000+ communes sans geler l'interface
- Envoie des mises à jour de progression régulières

### Responsabilités
- Charger toutes les données communes en mémoire
- Exécuter le filtrage géographique (formule de Haversine)
- Gérer les zones d'inclusion et d'exclusion
- Retourner jusqu'à 500 résultats avec services d'urgence

### Communication avec le thread principal

```javascript
// Dans app.js (thread principal)
worker.postMessage({ type: 'search', payload: searchParams });
worker.onmessage = (e) => {
    if (e.data.type === 'progress') updateProgressBar(e.data.progress);
    if (e.data.type === 'results') displayResults(e.data.results);
};

// Dans search-worker.js (Web Worker)
self.onmessage = async (e) => {
    const results = await handleSearch(e.data.payload);
    self.postMessage({ type: 'results', results });
};
```

---

## 3. Couche Application (JavaScript Frontend)

**Fichier principal** : `static/js/app.js` (1344+ lignes)

### Modules fonctionnels

| Module | Fonction |
|--------|----------|
| **Gestion des zones** | Ajout, suppression, édition des zones de recherche |
| **Autocomplétion** | Suggestions de villes avec normalisation française |
| **Import/Export CSV** | Chargement et sauvegarde des zones |
| **Affichage résultats** | Tableau triable, pagination, filtrage |
| **Cartographie** | Intégration Leaflet, cercles, marqueurs |
| **Partage** | Génération liens base64url, export fichiers |

### Patterns de conception

1. **Singleton Worker** : Un seul Web Worker pour toutes les recherches
2. **Event-driven** : Communication par événements entre composants
3. **Lazy Loading** : Données chargées à la première recherche
4. **URL State** : État de recherche encodé dans l'URL

---

## 4. Couche Présentation (HTML/CSS)

**Fichiers** : `index.html`, `results.html`, `static/css/app.css`

### Design System

```css
/* Palette de couleurs - Thème vert naturel */
--color-primary: #0b3d2e;      /* Vert foncé */
--color-primary-light: #e8f4ee; /* Vert très clair */
--color-accent: #2d7a5c;        /* Vert accent */
```

### Composants UI

| Composant | Description |
|-----------|-------------|
| **Tabs** | Navigation entre Liste, Carte, Urgences |
| **Data Table** | Tableau triable avec scroll horizontal |
| **Progress Bar** | Barre de progression animée |
| **Badges** | Indicateurs colorés (politique, wiki, référence) |
| **Modals** | Dialogues d'import CSV |

### Accessibilité

- Attributs ARIA pour lecteurs d'écran
- Navigation clavier (Tab, Flèches)
- Zones ARIA-live pour mises à jour dynamiques
- Contraste suffisant pour lisibilité

---

## Diagramme de séquence

```
┌─────────┐     ┌─────────┐     ┌──────────────┐     ┌─────────┐
│  User   │     │  app.js │     │search-worker │     │  JSON   │
└────┬────┘     └────┬────┘     └───────┬──────┘     └─────┬───┘
     │               │                  │                  │
     │  Clic Search  │                  │                  │
     │──────────────>│                  │                  │
     │               │                  │                  │
     │               │   postMessage    │                  │
     │               │  (search params) │                  │
     │               │─────────────────>│                  │
     │               │                  │                  │
     │               │                  │   Load data      │
     │               │                  │─────────────────>│
     │               │                  │<─────────────────│
     │               │                  │                  │
     │               │    progress      │                  │
     │               │<─────────────────│ (loop: calculs)  │
     │               │                  │                  │
     │               │    results       │                  │
     │               │<─────────────────│                  │
     │               │                  │                  │
     │  Affichage    │                  │                  │
     │<──────────────│                  │                  │
     │               │                  │                  │
```

---

