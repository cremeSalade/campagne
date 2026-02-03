# Moteur de Recherche

## Vue d'ensemble

Le moteur de recherche est implémenté dans un **Web Worker** (`static/js/search-worker.js`) pour ne pas bloquer l'interface utilisateur pendant les calculs intensifs sur plus de 36 000 communes.

---

## Algorithme de recherche

### Étape 1 : Chargement des données

```javascript
async function loadData() {
    const [communesResponse, urgencesResponse] = await Promise.all([
        fetch('data/communes_enrichies.json'),
        fetch('data/urgences_service_public.json')
    ]);
    communes = await communesResponse.json();
    urgences = await urgencesResponse.json();
}
```

Les données sont chargées une seule fois et gardées en mémoire.

---

### Étape 2 : Filtrage par zones

Chaque commune est testée contre les zones de recherche définies par l'utilisateur :

```javascript
// Zone d'inclusion : la commune doit être entre min et max km du centre
function isInInclusionZone(commune, zone) {
    const distance = haversineDistance(
        commune.latitude, commune.longitude,
        zone.lat, zone.lng
    );
    return distance >= zone.minRadius && distance <= zone.maxRadius;
}

// Zone d'exclusion : la commune ne doit PAS être dans la zone
function isInExclusionZone(commune, zone) {
    const distance = haversineDistance(
        commune.latitude, commune.longitude,
        zone.lat, zone.lng
    );
    return distance <= zone.radius;
}
```

---

### Étape 3 : Calcul de distance (Haversine)

La formule de Haversine calcule la distance entre deux points sur une sphère (la Terre) :

```javascript
function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Rayon de la Terre en km
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance en km
}

function toRad(deg) {
    return deg * (Math.PI / 180);
}
```

**Pourquoi Haversine ?** La distance euclidienne (ligne droite) serait inexacte car la Terre est une sphère. Haversine donne la distance réelle "à vol d'oiseau".

---

### Étape 4 : Classification politique

Le score d'extrême droite est catégorisé pour l'affichage :

```javascript
function getExtremeDroiteCategory(score) {
    if (score === null || score === undefined) return 'non-renseigne';
    if (score < 15) return 'tres-faible';   // Vert
    if (score < 25) return 'faible';         // Vert clair
    if (score < 35) return 'moyen';          // Jaune
    if (score < 45) return 'eleve';          // Orange
    if (score < 55) return 'tres-eleve';     // Rouge clair
    return 'extreme';                         // Rouge foncé
}
```

---

### Étape 5 : Recherche des urgences

Pour chaque zone de recherche, on trouve les services d'urgence à proximité :

```javascript
function getUrgencesInZones(zones) {
    const urgencesInZones = [];

    for (const urgence of urgences) {
        for (const zone of zones) {
            const distance = haversineDistance(
                urgence.latitude, urgence.longitude,
                zone.lat, zone.lng
            );

            if (distance <= zone.maxRadius) {
                urgencesInZones.push({
                    ...urgence,
                    distanceFromZone: distance,
                    zoneName: zone.name
                });
                break; // Éviter les doublons
            }
        }
    }

    return urgencesInZones;
}
```

---

### Étape 6 : Construction du résultat

Chaque commune correspondante est enrichie avec des données calculées :

```javascript
function buildResult(commune, inclusionZones) {
    // Trouver la zone d'inclusion la plus proche
    let minDistance = Infinity;
    let referenceCity = null;

    for (const zone of inclusionZones) {
        const distance = haversineDistance(
            commune.latitude, commune.longitude,
            zone.lat, zone.lng
        );
        if (distance < minDistance) {
            minDistance = distance;
            referenceCity = zone.name;
        }
    }

    // Trouver l'urgence la plus proche
    const nearestUrgence = findNearestUrgence(commune);

    return {
        nom: commune.nom,
        codePostal: commune.code_postal,
        population: commune.population,
        distance: Math.round(minDistance * 10) / 10,
        referenceCity: referenceCity,
        prixM2Appartement: commune.prix_m2_appartement,
        prixM2Maison: commune.prix_m2_maison,
        altitude: commune.altitude,
        temperatureMoyenne: commune.temperature_moyenne,
        extremeDroite: commune.extreme_droite,
        extremeDroiteCategory: getExtremeDroiteCategory(commune.extreme_droite),
        urgenceDistance: nearestUrgence?.distance,
        urgenceNom: nearestUrgence?.nom,
        latitude: commune.latitude,
        longitude: commune.longitude,
        hasWiki: commune.has_wiki
    };
}
```

---

## Flux complet de recherche

```javascript
async function handleSearch(params) {
    const { inclusionZones, exclusionZones, minPopulation, maxPopulation } = params;

    // 1. Charger les données si nécessaire
    if (!communes) await loadData();

    const results = [];
    const total = communes.length;

    // 2. Parcourir toutes les communes
    for (let i = 0; i < total; i++) {
        const commune = communes[i];

        // 3. Vérifier les coordonnées
        if (!commune.latitude || !commune.longitude) continue;

        // 4. Filtrer par population
        if (minPopulation && commune.population < minPopulation) continue;
        if (maxPopulation && commune.population > maxPopulation) continue;

        // 5. Vérifier les zones d'inclusion
        const isIncluded = inclusionZones.some(zone =>
            isInInclusionZone(commune, zone)
        );
        if (!isIncluded) continue;

        // 6. Vérifier les zones d'exclusion
        const isExcluded = exclusionZones.some(zone =>
            isInExclusionZone(commune, zone)
        );
        if (isExcluded) continue;

        // 7. Construire le résultat
        results.push(buildResult(commune, inclusionZones));

        // 8. Mettre à jour la progression
        if (i % 1000 === 0) {
            self.postMessage({
                type: 'progress',
                progress: Math.round((i / total) * 100)
            });
        }
    }

    // 9. Trier par distance et limiter à 500
    results.sort((a, b) => a.distance - b.distance);
    const topResults = results.slice(0, 500);

    // 10. Ajouter les urgences dans les zones
    const urgencesInZones = getUrgencesInZones(inclusionZones);

    return {
        communes: topResults,
        urgences: urgencesInZones,
        totalFound: results.length
    };
}
```

---

## Messages du Worker

### Messages entrants (du thread principal)

| Type | Payload | Description |
|------|---------|-------------|
| `search` | `{ inclusionZones, exclusionZones, minPop, maxPop }` | Lancer une recherche |
| `load` | - | Pré-charger les données |

### Messages sortants (vers le thread principal)

| Type | Data | Description |
|------|------|-------------|
| `progress` | `{ progress: 0-100 }` | Mise à jour progression |
| `results` | `{ communes, urgences, totalFound }` | Résultats de recherche |
| `loaded` | - | Données chargées |
| `error` | `{ message }` | Erreur rencontrée |

---

## Performance

- **36 000+ communes** traitées en quelques secondes
- Mises à jour de progression toutes les **1000 communes**
- Résultats limités à **500** pour éviter surcharge UI
- Données gardées en mémoire après premier chargement
- Calculs Haversine optimisés (pas de fonctions trigonométriques inutiles)

---

## Exemple d'utilisation

```javascript
// Dans app.js
const worker = new Worker('static/js/search-worker.js');

worker.postMessage({
    type: 'search',
    payload: {
        inclusionZones: [
            { name: 'Montpellier', lat: 43.6108, lng: 3.8767, minRadius: 10, maxRadius: 50 }
        ],
        exclusionZones: [
            { name: 'Nîmes', lat: 43.8367, lng: 4.3601, radius: 20 }
        ],
        minPopulation: 500,
        maxPopulation: 5000
    }
});

worker.onmessage = (e) => {
    switch (e.data.type) {
        case 'progress':
            updateProgressBar(e.data.progress);
            break;
        case 'results':
            displayResults(e.data.communes);
            displayUrgences(e.data.urgences);
            break;
    }
};
```
