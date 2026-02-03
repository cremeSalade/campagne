# Interface Utilisateur

## Vue d'ensemble

L'interface est divisée en deux pages principales :
- **index.html** : Page de recherche avec formulaire et résultats
- **results.html** : Page de visualisation des résultats partagés

Le code JavaScript principal est dans `static/js/app.js` (1600+ lignes).

---

## Composants principaux

### 1. Panneau de recherche

#### Autocomplétion des villes

```javascript
function searchCities(query) {
    const normalized = normalizeText(query);
    const matches = communesIndex.filter(c =>
        normalizeText(c.nom).includes(normalized)
    );
    return matches.slice(0, 8); // Max 8 suggestions
}

function normalizeText(text) {
    return text
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '') // Supprime accents
        .toUpperCase();
}
```

L'autocomplétion gère les accents français (é, è, ê → e).

#### Gestion des zones de recherche

Deux types de zones :
- **Zones d'inclusion** : Communes à inclure (entre rayon min et max)
- **Zones d'exclusion** : Communes à exclure (dans le rayon)

```javascript
const searchZones = {
    inclusion: [
        { name: 'Montpellier', lat: 43.61, lng: 3.87, minRadius: 10, maxRadius: 50 }
    ],
    exclusion: [
        { name: 'Nîmes', lat: 43.83, lng: 4.36, radius: 20 }
    ]
};
```

#### Import/Export CSV

```javascript
// Export
function exportZonesToCSV() {
    const rows = [['Type', 'Nom', 'Latitude', 'Longitude', 'Rayon Min', 'Rayon Max']];
    searchZones.inclusion.forEach(z => {
        rows.push(['inclusion', z.name, z.lat, z.lng, z.minRadius, z.maxRadius]);
    });
    // ... export as CSV file
}

// Import (détection automatique délimiteur)
function detectDelimiter(text) {
    const delimiters = [',', ';', '\t'];
    return delimiters.reduce((best, d) =>
        (text.split(d).length > text.split(best).length) ? d : best
    );
}
```

---

### 2. Système d'onglets

L'interface utilise 4 onglets :

| Onglet | Contenu |
|--------|---------|
| **Liste** | Tableau triable des communes |
| **Carte** | Carte Leaflet avec zones et marqueurs |
| **Urgences** | Services d'urgence trouvés |
| **Carte Urgences** | Carte dédiée aux urgences |

```javascript
// Navigation clavier
tabList.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') selectNextTab();
    if (e.key === 'ArrowLeft') selectPrevTab();
});
```

---

### 3. Tableau de résultats

#### Colonnes affichées

| Colonne | Description | Tri |
|---------|-------------|-----|
| Commune | Nom de la ville | A-Z |
| Code postal | Code postal | Num |
| Population | Nombre d'habitants | Num |
| Distance | Distance au centre de zone | Num |
| Prix appart. | Prix/m² appartement | Num |
| Prix maison | Prix/m² maison | Num |
| Altitude | Altitude en mètres | Num |
| Température | Température moyenne | Num |
| Extrême droite | Score politique (%) | Num |
| Urgence | Distance à l'urgence la plus proche | Num |

#### Tri des colonnes

```javascript
function sortResults(column, direction) {
    results.sort((a, b) => {
        let valueA = a[column];
        let valueB = b[column];

        // Gestion des valeurs nulles
        if (valueA === null) return 1;
        if (valueB === null) return -1;

        // Tri numérique ou alphabétique
        if (typeof valueA === 'number') {
            return direction === 'asc' ? valueA - valueB : valueB - valueA;
        }
        return direction === 'asc'
            ? valueA.localeCompare(valueB, 'fr')
            : valueB.localeCompare(valueA, 'fr');
    });
}
```

---

### 4. Carte Leaflet

#### Initialisation

```javascript
const map = L.map('map').setView([46.2276, 2.2137], 6); // Centre France

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);
```

#### Affichage des zones de recherche

```javascript
function drawSearchZones() {
    // Zone d'inclusion (anneau entre minRadius et maxRadius)
    searchZones.inclusion.forEach(zone => {
        L.circle([zone.lat, zone.lng], {
            radius: zone.maxRadius * 1000, // km → m
            color: '#2d7a5c',
            fillOpacity: 0.1
        }).addTo(map);

        L.circle([zone.lat, zone.lng], {
            radius: zone.minRadius * 1000,
            color: '#2d7a5c',
            fillOpacity: 0,
            dashArray: '5, 5'
        }).addTo(map);
    });

    // Zone d'exclusion (rouge)
    searchZones.exclusion.forEach(zone => {
        L.circle([zone.lat, zone.lng], {
            radius: zone.radius * 1000,
            color: '#dc3545',
            fillOpacity: 0.2
        }).addTo(map);
    });
}
```

#### Marqueurs de résultats

```javascript
function addResultMarkers(results) {
    results.forEach(commune => {
        const color = getMarkerColor(commune);
        const marker = L.circleMarker([commune.latitude, commune.longitude], {
            radius: 6,
            fillColor: color,
            fillOpacity: 0.8
        });

        marker.bindPopup(`
            <strong>${commune.nom}</strong><br>
            Population: ${commune.population.toLocaleString('fr-FR')}<br>
            Distance: ${commune.distance} km<br>
            Prix/m²: ${commune.prixM2Maison || 'N/A'} €
        `);

        marker.addTo(map);
    });
}

function getMarkerColor(commune) {
    // Bleu pour ville de référence, sinon selon score politique
    if (commune.isReference) return '#0066cc';

    const category = commune.extremeDroiteCategory;
    const colors = {
        'tres-faible': '#28a745',
        'faible': '#7cb342',
        'moyen': '#ffc107',
        'eleve': '#ff9800',
        'tres-eleve': '#f44336',
        'extreme': '#b71c1c'
    };
    return colors[category] || '#666666';
}
```

---

### 5. Export des résultats

#### Export CSV

```javascript
function exportCSV() {
    const BOM = '\uFEFF'; // Pour Excel
    const headers = ['Commune', 'Code postal', 'Population', 'Distance', ...];
    const rows = results.map(r => [r.nom, r.codePostal, r.population, r.distance, ...]);

    const csv = BOM + [headers, ...rows]
        .map(row => row.map(cell => `"${cell}"`).join(';'))
        .join('\n');

    downloadFile(csv, 'resultats.csv', 'text/csv;charset=utf-8');
}
```

#### Export JSON

```javascript
function exportJSON() {
    const data = {
        searchParams: {
            inclusionZones: searchZones.inclusion,
            exclusionZones: searchZones.exclusion,
            minPopulation,
            maxPopulation
        },
        results: results,
        exportDate: new Date().toISOString()
    };

    downloadFile(JSON.stringify(data, null, 2), 'resultats.json', 'application/json');
}
```

#### Lien partageable

```javascript
function generateShareableLink() {
    const data = {
        zones: searchZones,
        pop: { min: minPopulation, max: maxPopulation },
        timestamp: Date.now()
    };

    const encoded = base64UrlEncode(JSON.stringify(data));
    return `${window.location.origin}/results.html?q=${encoded}`;
}

function base64UrlEncode(str) {
    return btoa(unescape(encodeURIComponent(str)))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
}
```

---

### 6. Badges et indicateurs

#### Badge politique

```html
<span class="badge badge-politique badge-${category}">
    ${score}%
</span>
```

```css
.badge-tres-faible { background: #28a745; }
.badge-faible { background: #7cb342; }
.badge-moyen { background: #ffc107; color: #000; }
.badge-eleve { background: #ff9800; }
.badge-tres-eleve { background: #f44336; }
.badge-extreme { background: #b71c1c; }
```

#### Badge Wikipedia

```html
<span class="badge badge-wiki" title="Article Wikipedia disponible">W</span>
```

#### Badge ville de référence

```html
<span class="badge badge-reference">Réf: Montpellier</span>
```

---

## Design System

### Palette de couleurs

| Variable | Valeur | Usage |
|----------|--------|-------|
| `--primary` | #0b3d2e | Fond header, boutons |
| `--primary-light` | #e8f4ee | Fond clair |
| `--accent` | #2d7a5c | Liens, hover |
| `--text` | #333333 | Texte principal |
| `--border` | #dee2e6 | Bordures |

### Typographie

- **Titres** : Fraunces (serif)
- **Corps** : Source Sans 3 (sans-serif)
- **Code** : Monospace système

### Responsive

```css
@media (max-width: 768px) {
    .search-form { flex-direction: column; }
    .results-table { font-size: 14px; }
    .tab-button { padding: 8px 12px; }
}
```

---

## Accessibilité

- `aria-label` sur tous les boutons
- `aria-live="polite"` pour mises à jour dynamiques
- Navigation clavier complète
- Contraste minimum 4.5:1
- Focus visible sur éléments interactifs
