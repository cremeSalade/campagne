# Données et Scripts

## Vue d'ensemble

Les données sont le coeur de l'application. Elles proviennent d'un fichier CSV source qui est transformé en fichiers JSON optimisés pour le web.

---

## Structure des données

### Fichier source : `communes_enrichies.csv`

Fichier CSV de ~7MB contenant toutes les données brutes pour 36 000+ communes françaises.

| Colonne | Type | Description |
|---------|------|-------------|
| `nom` | string | Nom de la commune |
| `code_postal` | string | Code postal (5 chiffres) |
| `population` | int | Nombre d'habitants |
| `latitude` | float | Latitude GPS |
| `longitude` | float | Longitude GPS |
| `altitude` | int | Altitude en mètres |
| `prix_m2_appartement` | float | Prix moyen au m² (appart) |
| `prix_m2_maison` | float | Prix moyen au m² (maison) |
| `temperature_moyenne` | float | Température annuelle moyenne |
| `extreme_droite` | float | % vote extrême droite |
| `has_wiki` | bool | Article Wikipedia existe |

---

### Fichiers JSON générés

#### 1. `communes_enrichies.json` (17MB)

Base de données complète de toutes les communes.

```json
[
    {
        "nom": "MONTPELLIER",
        "code_postal": "34000",
        "population": 290053,
        "latitude": 43.6108,
        "longitude": 3.8767,
        "altitude": 27,
        "prix_m2_appartement": 3542,
        "prix_m2_maison": 3891,
        "temperature_moyenne": 15.2,
        "extreme_droite": 18.5,
        "has_wiki": true
    },
    // ... 36000+ communes
]
```

#### 2. `communes_index.json` (4.8MB)

Index léger pour l'autocomplétion (chargé en priorité).

```json
[
    {
        "nom": "MONTPELLIER",
        "latitude": 43.6108,
        "longitude": 3.8767,
        "population": 290053
    },
    // ...
]
```

#### 3. `urgences_service_public.json` (300KB+)

Services d'urgence (hôpitaux, SAMU, etc.).

```json
[
    {
        "nom": "CHU Montpellier - Lapeyronie",
        "type": "Public",
        "latitude": 43.6322,
        "longitude": 3.8454,
        "adresse": "371 Avenue du Doyen Gaston Giraud",
        "telephone": "04 67 33 67 33"
    },
    // ...
]
```

#### 4. `meta.json` (<1KB)

Métadonnées sur le dataset.

```json
{
    "totalCommunes": 36542,
    "totalUrgences": 1247,
    "lastUpdate": "2026-01-15",
    "version": "1.0"
}
```

---

## Script de build : `build_data.py`

### Utilisation

```bash
cd scripts
python build_data.py
```

### Fonctions principales

#### Normalisation des noms

```python
def normalize_name(name):
    """
    Normalise les noms français pour la recherche.
    Ex: "Saint-Étienne-du-Rouvray" → "SAINT-ETIENNE-DU-ROUVRAY"
    """
    import unicodedata
    # Décompose les caractères accentués
    normalized = unicodedata.normalize('NFD', name)
    # Supprime les accents (catégorie Mn = Mark, Nonspacing)
    without_accents = ''.join(
        c for c in normalized
        if unicodedata.category(c) != 'Mn'
    )
    return without_accents.upper()
```

#### Conversion sécurisée

```python
def to_float(value, default=None):
    """Convertit en float avec gestion des erreurs."""
    if value is None or value == '':
        return default
    try:
        return float(str(value).replace(',', '.'))
    except (ValueError, TypeError):
        return default

def to_int(value, default=None):
    """Convertit en int avec gestion des erreurs."""
    if value is None or value == '':
        return default
    try:
        return int(float(str(value).replace(',', '.')))
    except (ValueError, TypeError):
        return default
```

#### Lecture et traitement

```python
def read_communes(csv_path):
    """Lit le CSV et génère les structures JSON."""
    communes = []
    index = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')

        for row in reader:
            # Données complètes
            commune = {
                'nom': normalize_name(row['nom']),
                'code_postal': row['code_postal'],
                'population': to_int(row['population']),
                'latitude': to_float(row['latitude']),
                'longitude': to_float(row['longitude']),
                'altitude': to_int(row['altitude']),
                'prix_m2_appartement': to_float(row['prix_m2_appartement']),
                'prix_m2_maison': to_float(row['prix_m2_maison']),
                'temperature_moyenne': to_float(row['temperature_moyenne']),
                'extreme_droite': to_float(row['extreme_droite']),
                'has_wiki': row.get('has_wiki', '').lower() == 'true'
            }
            communes.append(commune)

            # Index léger
            index.append({
                'nom': commune['nom'],
                'latitude': commune['latitude'],
                'longitude': commune['longitude'],
                'population': commune['population']
            })

    return communes, index
```

#### Écriture JSON optimisée

```python
def write_json(data, output_path, indent=None):
    """Écrit un fichier JSON avec options de compression."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(
            data, f,
            ensure_ascii=False,  # Garde les caractères Unicode
            indent=indent,        # None = compact, 2 = lisible
            separators=(',', ':') if indent is None else None
        )
```

---

## Script de correction : `fix_missing_coords.py`

Corrige les communes avec coordonnées manquantes en utilisant des sources de secours.

```python
def fix_missing_coords(communes, fallback_source):
    """
    Remplit les coordonnées manquantes depuis une source de secours.
    """
    fixed_count = 0

    for commune in communes:
        if commune['latitude'] is None or commune['longitude'] is None:
            # Chercher dans la source de secours
            fallback = find_in_fallback(commune['nom'], fallback_source)
            if fallback:
                commune['latitude'] = fallback['latitude']
                commune['longitude'] = fallback['longitude']
                fixed_count += 1

    print(f"Coordonnées corrigées: {fixed_count}")
    return communes
```

---

## Qualité des données

### Validations effectuées

| Validation | Description |
|------------|-------------|
| Coordonnées | latitude entre 41° et 51°, longitude entre -5° et 10° |
| Population | Entier positif |
| Code postal | 5 chiffres |
| Prix | Positif ou null |
| Température | Entre -10° et 30° |

### Données manquantes

Certains champs peuvent être `null` :
- Prix au m² (petites communes sans transactions)
- Score extrême droite (communes sans bureau de vote)
- Température moyenne (données météo incomplètes)

L'interface gère ces cas avec "N/A" ou en les excluant du tri.

---

## Mise à jour des données

### Processus de mise à jour

1. Obtenir un nouveau fichier `communes_enrichies.csv`
2. Exécuter le script de build :
   ```bash
   python scripts/build_data.py
   ```
3. Vérifier les fichiers générés dans `data/`
4. Tester l'application localement
5. Déployer les nouveaux fichiers

### Sources de données (externes)

| Donnée | Source probable |
|--------|-----------------|
| Communes | INSEE - Code Officiel Géographique |
| Population | INSEE - Recensement |
| Coordonnées | IGN / OpenStreetMap |
| Prix immobilier | DVF (Demandes de Valeurs Foncières) |
| Température | Météo France |
| Vote | Ministère de l'Intérieur |
| Urgences | Service-Public.fr |

---

## Optimisations

### Taille des fichiers

| Fichier | Brut | Compressé (gzip) |
|---------|------|------------------|
| communes_enrichies.json | 17MB | ~3MB |
| communes_index.json | 4.8MB | ~800KB |
| urgences_service_public.json | 300KB | ~50KB |

### Stratégie de chargement

1. **Index d'abord** : `communes_index.json` chargé pour autocomplétion
2. **Données complètes** : `communes_enrichies.json` chargé à la première recherche
3. **Urgences** : Chargé en parallèle avec les données complètes

```javascript
// Chargement parallèle optimisé
const [communes, urgences] = await Promise.all([
    fetch('data/communes_enrichies.json').then(r => r.json()),
    fetch('data/urgences_service_public.json').then(r => r.json())
]);
```
