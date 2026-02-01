// Variables globales
let searchZones = [];  // Nouvelle structure: {name, lat, lon, rayonMin, rayonMax, exclure}
let searchResults = [];
let urgencesData = [];  // Services d'urgence dans la zone
let currentSort = { column: 'distance', direction: 'asc' };
let map = null;
let markersLayer = null;
let urgencesMap = null;
let urgencesMarkersLayer = null;
let autocompleteTimeout = null;

let communesIndex = [];
let indexLoaded = false;
let searchWorker = null;
let workerRequestId = 0;
const workerRequests = new Map();

function debugLog(message, payload) {
    if (payload !== undefined) {
        console.log(`[DEBUG] ${message}`, payload);
    } else {
        console.log(`[DEBUG] ${message}`);
    }
}


// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    loadIndexAndStats();
    setupScrollTop();

    // Pas de ville par défaut - l'utilisateur doit en ajouter une
});

function setupScrollTop() {
    const scrollBtn = document.getElementById('scroll-top');
    if (!scrollBtn) return;

    const onScroll = () => {
        if (window.scrollY > 400) {
            scrollBtn.classList.add('is-visible');
        } else {
            scrollBtn.classList.remove('is-visible');
        }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    scrollBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}


// === Donnees locales ===
function dataUrl(path) {
    return new URL(path, window.location).toString();
}

function normalizeName(value) {
    if (!value) return "";
    return value
        .toString()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toUpperCase()
        .trim();
}


function detectCsvDelimiter(line) {
    if (line.includes(';')) return ';';
    if (line.includes('\t')) return '\t';
    return ',';
}

function splitCsvLine(line, delimiter) {
    return line.split(delimiter).map(cell => cell.trim());
}

function zonesToCsv(zones) {
    const header = 'name,lat,lon,rayon_min,rayon_max,exclure';
    const rows = zones.map(z => {
        const exclure = z.exclure ? 'true' : 'false';
        return `${z.name},${z.lat ?? ''},${z.lon ?? ''},${z.rayonMin ?? 0},${z.rayonMax ?? 100},${exclure}`;
    });
    return [header, ...rows].join('\n');
}

async function parseZonesCsv(textValue) {
    const lines = textValue.split(/\r?\n/).map(l => l.trim()).filter(Boolean).filter(l => !l.startsWith('#'));
    if (lines.length === 0) {
        return { zones: [], errors: ['CSV vide'] };
    }

    const delimiter = detectCsvDelimiter(lines[0]);
    let startIndex = 0;
    let columns = ['name', 'lat', 'lon', 'rayon_min', 'rayon_max', 'exclure'];

    const headerCells = splitCsvLine(lines[0], delimiter).map(c => c.toLowerCase());
    if (headerCells.some(c => ['name', 'nom', 'lat', 'lon'].includes(c))) {
        columns = headerCells.map(c => {
            if (c === 'nom') return 'name';
            if (c === 'rayonmin') return 'rayon_min';
            if (c === 'rayonmax') return 'rayon_max';
            return c;
        });
        startIndex = 1;
    }

    const zones = [];
    const errors = [];

    for (let i = startIndex; i < lines.length; i++) {
        const cells = splitCsvLine(lines[i], delimiter);
        const row = {};
        columns.forEach((col, idx) => {
            row[col] = cells[idx] ?? '';
        });

        const name = row.name || '';
        let lat = row.lat ? parseFloat(row.lat.replace(',', '.')) : null;
        let lon = row.lon ? parseFloat(row.lon.replace(',', '.')) : null;
        const rayonMin = row.rayon_min ? parseFloat(row.rayon_min.replace(',', '.')) : 0;
        const rayonMax = row.rayon_max ? parseFloat(row.rayon_max.replace(',', '.')) : 100;
        const exclure = ['true', '1', 'yes', 'oui'].includes((row.exclure || '').toString().toLowerCase());

        if ((!lat || !lon) && name) {
            await ensureIndexLoaded();
            const city = findBestCityByName(name);
            if (city) {
                lat = city.lat;
                lon = city.lon;
            }
        }

        if (!name) {
            errors.push(`Ligne ${i + 1}: nom manquant`);
            continue;
        }
        if (lat == null || lon == null || Number.isNaN(lat) || Number.isNaN(lon)) {
            errors.push(`Ligne ${i + 1}: coordonnees invalides pour ${name}`);
            continue;
        }
        if (Number.isNaN(rayonMin) || Number.isNaN(rayonMax) || rayonMin >= rayonMax) {
            errors.push(`Ligne ${i + 1}: rayon min/max invalide pour ${name}`);
            continue;
        }

        zones.push({
            name,
            lat,
            lon,
            rayonMin,
            rayonMax,
            exclure
        });
    }

    return { zones, errors };
}

function showCsvErrors(errors) {
    const errorDiv = document.getElementById('zones-csv-errors');
    if (!errorDiv) return;
    if (!errors || errors.length === 0) {
        errorDiv.classList.add('hidden');
        errorDiv.textContent = '';
        return;
    }
    errorDiv.classList.remove('hidden');
    errorDiv.innerHTML = errors.map(e => `<div>${e}</div>`).join('');
}

async function applyZonesCsv() {
    const textarea = document.getElementById('zones-csv');
    if (!textarea) return;

    const parsed = await parseZonesCsv(textarea.value || '');
    if (parsed.errors.length) {
        showCsvErrors(parsed.errors);
        return;
    }

    showCsvErrors([]);
    searchZones = parsed.zones;
    updateSearchZonesList();
}

function loadZonesCsv() {
    const textarea = document.getElementById('zones-csv');
    if (!textarea) return;
    textarea.value = zonesToCsv(searchZones);
    showCsvErrors([]);
}

function clearZonesCsv() {
    const textarea = document.getElementById('zones-csv');
    if (!textarea) return;
    textarea.value = '';
    showCsvErrors([]);
}
async function loadIndexAndStats() {
    try {
        const [indexRes, metaRes] = await Promise.all([
            fetch(dataUrl('data/communes_index.json')),
            fetch(dataUrl('data/meta.json')).catch(() => null)
        ]);

        if (!indexRes.ok) {
            throw new Error('Impossible de charger communes_index.json');
        }

        communesIndex = await indexRes.json();
        indexLoaded = true;

        let totalCommunes = communesIndex.length;
        if (metaRes && metaRes.ok) {
            const meta = await metaRes.json();
            if (meta && meta.total_communes) {
                totalCommunes = meta.total_communes;
            }
        }

        const prixEl = document.getElementById('stat-communes-prix');
        const coordsEl = document.getElementById('stat-communes-coords');
        if (prixEl) prixEl.textContent = totalCommunes.toLocaleString('fr-FR');
        if (coordsEl) coordsEl.textContent = totalCommunes.toLocaleString('fr-FR');
    } catch (error) {
        console.error('Erreur chargement index:', error);
        showError('Impossible de charger les donnees locales (index).');
    }
}

async function ensureIndexLoaded() {
    if (!indexLoaded) {
        await loadIndexAndStats();
    }
}

function findBestCityByName(name) {
    const normalized = normalizeName(name);
    let best = null;

    for (const city of communesIndex) {
        if (city.normalized !== normalized) continue;
        if (!best || (city.population || 0) > (best.population || 0)) {
            best = city;
        }
    }

    return best;
}

function suggestCities(query) {
    const normalizedQuery = normalizeName(query);
    if (!normalizedQuery) return [];

    const matches = [];

    for (const city of communesIndex) {
        if (!city.normalized) continue;
        let score = 0;
        if (city.normalized.startsWith(normalizedQuery)) {
            score = 2;
        } else if (city.normalized.includes(normalizedQuery)) {
            score = 1;
        }

        if (score > 0) {
            matches.push({
                ...city,
                score
            });
        }
    }

    matches.sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        return (b.population || 0) - (a.population || 0);
    });

    return matches.slice(0, 8).map(city => ({
        name: city.name,
        code_postal: city.code_postal,
        population: city.population,
        lat: city.lat,
        lon: city.lon
    }));
}

function base64UrlEncode(payload) {
    const json = JSON.stringify(payload);
    const bytes = new TextEncoder().encode(json);
    let binary = '';
    bytes.forEach(b => {
        binary += String.fromCharCode(b);
    });
    const base64 = btoa(binary);
    return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function getSearchWorker() {
    if (searchWorker) return searchWorker;

    searchWorker = new Worker('./static/js/search-worker.js?v=20260202c');
    searchWorker.onmessage = event => {
        const data = event.data || {};
        const request = workerRequests.get(data.id);

        if (data.type === 'progress') {
            if (request && request.onProgress) {
                request.onProgress(data);
            }
            return;
        }

        if (data.type === 'result') {
            if (request) {
                request.resolve(data);
                workerRequests.delete(data.id);
            }
            return;
        }

        if (data.type === 'error') {
            if (request) {
                request.reject(new Error(data.message || 'Erreur inconnue'));
                workerRequests.delete(data.id);
            } else {
                console.error(data.message);
            }
        }
    };

    return searchWorker;
}

function runSearch(params, onProgress) {
    const worker = getSearchWorker();
    const id = workerRequestId + 1;
    workerRequestId = id;

    return new Promise((resolve, reject) => {
        workerRequests.set(id, { resolve, reject, onProgress });
        worker.postMessage({ type: 'search', id, params });
    });
}


// Gestion des onglets
function switchTab(tabName) {
    // Mettre a jour les boutons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    const activeBtn = document.getElementById(`tab-${tabName}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Afficher le bon contenu
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    document.getElementById(`${tabName}-view`).classList.remove('hidden');
    
    // Rafraîchir la carte si on passe sur l'onglet carte
    if (tabName === 'map' && map) {
        setTimeout(() => {
            map.invalidateSize();
            if (searchResults.length > 0) {
                updateMap();
            }
        }, 100);
    }

    // Rafraîchir la carte urgences si on passe sur cet onglet
    if (tabName === 'urgences-map') {
        setTimeout(() => {
            if (urgencesMap) {
                urgencesMap.invalidateSize();
            }
            updateUrgencesMap();
        }, 100);
    }
}

// Initialiser la carte
function initMap() {
    map = L.map('map').setView([46.5, 2.5], 6);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
    
    markersLayer = L.layerGroup().addTo(map);
}

// Ajouter une zone de recherche
async function addSearchZone() {
    const cityName = document.getElementById('city-search').value.trim();

    if (!cityName) {
        alert('Veuillez entrer un nom de ville');
        return;
    }

    try {
        debugLog('addSearchZone lookup', cityName);
        await ensureIndexLoaded();
        const city = findBestCityByName(cityName);

        if (city) {
            debugLog('addSearchZone found city', city);
            addSearchZoneData(city.name, city.lat, city.lon);
            document.getElementById('city-search').value = '';
        } else {
            alert('Ville non trouvee');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la recherche de la ville');
    }
}

// Ajouter une zone de recherche avec ses donnees
function addSearchZoneData(name, lat, lon) {
    if (searchZones.some(z => z.name === name)) {
        alert('Cette ville est deja dans la liste');
        return;
    }

    debugLog('addSearchZoneData', { name, lat, lon });
    searchZones.push({
        name,
        lat,
        lon,
        rayonMin: 0,
        rayonMax: 100,
        exclure: false
    });
    updateSearchZonesList();
}

// Mettre a jour la liste des zones de recherche (cartouches)
function updateSearchZonesList() {
    debugLog('updateSearchZonesList', searchZones.length);
    const container = document.getElementById('search-zones');
    container.innerHTML = '';

    searchZones.forEach((zone, index) => {
        const zoneDiv = document.createElement('div');
        const isExclude = zone.exclure === true;
        zoneDiv.className = `zone-card${isExclude ? ' zone-card--exclude' : ''}`;
        zoneDiv.innerHTML = `
            <div class="zone-header">
                <div>
                    <div class="zone-title">${zone.name}</div>
                    ${isExclude ? '<span class="zone-badge">Exclusion</span>' : ''}
                </div>
                <button type="button" onclick="removeSearchZone(${index})" class="btn btn-ghost btn-icon" style="padding:6px 10px;">
                    Retirer
                </button>
            </div>
            <div class="zone-fields">
                <div>
                    <label class="field-label" style="text-transform:none; letter-spacing:0;">Rayon min (km)</label>
                    <input type="number" value="${zone.rayonMin}" min="0"
                        onchange="updateZoneParam(${index}, 'rayonMin', parseInt(this.value))"
                        class="input input-inline">
                </div>
                <div>
                    <label class="field-label" style="text-transform:none; letter-spacing:0;">Rayon max (km)</label>
                    <input type="number" value="${zone.rayonMax}" min="0"
                        onchange="updateZoneParam(${index}, 'rayonMax', parseInt(this.value))"
                        class="input input-inline">
                </div>
                <div style="display:flex; align-items:flex-end;">
                    <label class="checkbox">
                        <input type="checkbox" ${zone.exclure ? 'checked' : ''}
                            onchange="updateZoneParam(${index}, 'exclure', this.checked)">
                        Exclure
                    </label>
                </div>
            </div>
        `;
        container.appendChild(zoneDiv);
    });
}

// Retirer une zone de recherche
function removeSearchZone(index) {
    debugLog('removeSearchZone', index);
    searchZones.splice(index, 1);
    updateSearchZonesList();
}

// Mettre a jour un parametre d'une zone
function updateZoneParam(index, param, value) {
    if (index >= 0 && index < searchZones.length) {
        searchZones[index][param] = value;
        if (param === 'exclure') {
            updateSearchZonesList();
        }
    }
}

// === Autocomplete des villes ===

async function onCitySearchInput(value) {
    clearTimeout(autocompleteTimeout);

    const dropdown = document.getElementById('autocomplete-dropdown');

    if (!value || value.length < 2) {
        dropdown.classList.add('hidden');
        return;
    }

    autocompleteTimeout = setTimeout(async () => {
        try {
            debugLog('autocomplete query', value);
            await ensureIndexLoaded();
            const suggestions = suggestCities(value);
            debugLog('autocomplete suggestions', suggestions.length);

            if (suggestions.length > 0) {
                dropdown.innerHTML = suggestions.map(city => `
                    <li onclick="selectAutocompleteCity('${city.name.replace(/'/g, "\\'")}', ${city.lat}, ${city.lon})">
                        <div class="autocomplete-title">${city.name}</div>
                        <div class="autocomplete-meta">${city.code_postal || ''} - ${(city.population || 0).toLocaleString('fr-FR')} habitants</div>
                    </li>
                `).join('');
                dropdown.classList.remove('hidden');
            } else {
                dropdown.innerHTML = '<li><div class="autocomplete-meta">Aucune ville trouvee</div></li>';
                dropdown.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Erreur autocomplete:', error);
            dropdown.classList.add('hidden');
        }
    }, 200);
}

function selectAutocompleteCity(name, lat, lon) {
    addSearchZoneData(name, lat, lon);
    document.getElementById('city-search').value = '';
    document.getElementById('autocomplete-dropdown').classList.add('hidden');
}

// Fermer le dropdown en cliquant ailleurs
document.addEventListener('click', function(e) {
    const dropdown = document.getElementById('autocomplete-dropdown');
    const searchInput = document.getElementById('city-search');
    if (dropdown && searchInput && !searchInput.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});

// Afficher une erreur dans l'interface (non-bloquant)
function showError(message) {
    const infoDiv = document.getElementById('results-info');
    infoDiv.classList.remove('hidden', 'alert--info');
    infoDiv.classList.add('alert--error');
    infoDiv.querySelector('p').textContent = 'Erreur: ' + message;
}

// Afficher les resultats
function displayResults(results) {
    const container = document.getElementById('results-list');

    if (!results || results.length === 0) {
        container.innerHTML = '<p class="muted" style="text-align:center; padding:24px;">Aucun resultat trouve</p>';
        return;
    }

    const computeBreaks = (field) => {
        const values = results
            .map(item => item[field])
            .filter(value => typeof value === 'number' && !Number.isNaN(value))
            .sort((a, b) => a - b);
        if (values.length < 4) return null;
        const quantile = (p) => values[Math.floor((values.length - 1) * p)];
        return {
            p25: quantile(0.25),
            p50: quantile(0.5),
            p75: quantile(0.75)
        };
    };

    const pricePill = (value, breaks) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
            return '<span class="muted">-</span>';
        }
        let cls = 'price-pill--mid';
        if (breaks) {
            if (value <= breaks.p25) cls = 'price-pill--low';
            else if (value <= breaks.p50) cls = 'price-pill--mid';
            else if (value <= breaks.p75) cls = 'price-pill--high';
            else cls = 'price-pill--very-high';
        } else if (value < 1500) {
            cls = 'price-pill--low';
        } else if (value < 3000) {
            cls = 'price-pill--mid';
        } else if (value < 4500) {
            cls = 'price-pill--high';
        } else {
            cls = 'price-pill--very-high';
        }
        return `<span class="price-pill ${cls}">${Math.round(value)} EUR/m2</span>`;
    };

    const sortableHeader = (column, label, align = 'left', extraClass = '') => {
        const indicator = currentSort.column === column
            ? (currentSort.direction === 'asc' ? '&#9650;' : '&#9660;')
            : '';
        const alignClass = align === 'center' ? 'cell-center' : align === 'right' ? 'cell-right' : '';
        const indicatorHtml = indicator ? `<span class="sort-indicator">${indicator}</span>` : '';
        return `<th class="sortable ${alignClass} ${extraClass}" onclick="sortResults('${column}')">${label}${indicatorHtml}</th>`;
    };

    const apptBreaks = computeBreaks('prix_m2_appartement');
    const maisonBreaks = computeBreaks('prix_m2_maison');

    let html = '<div class="table-wrap"><table class="data-table">';
    html += '<thead><tr>';
    html += sortableHeader('nom', 'Ville', 'left', 'col-name');
    html += '<th class="cell-center">Wiki</th>';
    html += sortableHeader('code_postal', 'CP');
    html += sortableHeader('population', 'Population', 'right');
    html += sortableHeader('distance', 'Distance', 'right');
    html += sortableHeader('prix_m2_appartement', 'Prix m2 appt', 'right', 'col-price');
    html += sortableHeader('prix_m2_maison', 'Prix m2 maison', 'right', 'col-price');
    html += sortableHeader('ville_reference', 'Proche de');
    html += sortableHeader('altitude', 'Altitude', 'right');
    html += sortableHeader('temperature', 'Temp.', 'right', 'col-temp');
    html += sortableHeader('score_extreme_droite', 'Ext. droite', 'left', 'col-ed');
    html += sortableHeader('distance_urgence', 'Urgence', 'right');
    html += '</tr></thead><tbody>';

    results.forEach(city => {
        const wikiLink = city.wikipedia_url
            ? `<a href="${city.wikipedia_url}" target="_blank" rel="noopener noreferrer" class="badge badge--ref" title="Wikipedia">Wiki</a>`
            : '<span class="muted">-</span>';

        const isReference = city.is_reference === true;
        const rowClass = isReference ? 'row-reference' : '';
        const nomDisplay = isReference
            ? `<span class="no-wrap"><strong>${city.nom}</strong> <span class="badge badge--ref">Ref</span></span>`
            : `<span class="no-wrap">${city.nom}</span>`;

        let edHtml = '-';
        if (city.categorie_extreme_droite) {
            const scorePercent = city.score_extreme_droite !== null && city.score_extreme_droite !== undefined
                ? ` (${Math.round(city.score_extreme_droite * 100)}%)`
                : '';
            edHtml = `<span class="badge no-wrap" style="background-color: ${city.couleur_extreme_droite}20; color: ${city.couleur_extreme_droite}; border: 1px solid ${city.couleur_extreme_droite};">${city.categorie_extreme_droite}${scorePercent}</span>`;
        }

        let urgenceHtml = '-';
        if (city.distance_urgence !== null && city.distance_urgence !== undefined) {
            urgenceHtml = `<div class="text-urgent">${city.distance_urgence} km</div>`;
            if (city.urgence_proche) {
                urgenceHtml += `<div class="muted">${city.urgence_proche}</div>`;
            }
        }

        const distanceValue = city.distance !== null && city.distance !== undefined ? `${city.distance} km` : '-';
        const altitudeValue = city.altitude !== null && city.altitude !== undefined ? `${Math.round(city.altitude)} m` : '-';
        const temperatureValue = city.temperature !== null && city.temperature !== undefined ? `<span class="no-wrap">${city.temperature} C</span>` : '-';
        const populationValue = city.population ? city.population.toLocaleString('fr-FR') : '-';
        const villeReference = isReference ? '-' : (city.ville_reference || '-');

        html += `<tr class="${rowClass}">`;
        html += `<td class="col-name">${nomDisplay}</td>`;
        html += `<td class="cell-center">${wikiLink}</td>`;
        html += `<td>${city.code_postal || '-'}</td>`;
        html += `<td class="cell-right">${populationValue}</td>`;
        html += `<td class="cell-right">${distanceValue}</td>`;
        html += `<td class="cell-right col-price">${pricePill(city.prix_m2_appartement, apptBreaks)}</td>`;
        html += `<td class="cell-right col-price">${pricePill(city.prix_m2_maison, maisonBreaks)}</td>`;
        html += `<td>${villeReference}</td>`;
        html += `<td class="cell-right">${altitudeValue}</td>`;
        html += `<td class="cell-right col-temp">${temperatureValue}</td>`;
        html += `<td class="col-ed">${edHtml}</td>`;
        html += `<td class="cell-right">${urgenceHtml}</td>`;
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    container.innerHTML = html;
}



function normalizeCategoryLabel(value) {
    if (!value) return '';
    return value
        .toString()
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .toLowerCase();
}

// Mettre a jour la carte
function updateMap() {
    debugLog('updateMap zones', searchZones);
    if (!map) return;

    markersLayer.clearLayers();

    searchZones.forEach(zone => {
        if (zone.lat == null || zone.lon == null || Number.isNaN(zone.lat) || Number.isNaN(zone.lon)) {
            debugLog('zone skip invalid coords', zone);
            return;
        }
        const isExclusion = zone.exclure;
        const color = isExclusion ? '#dc2626' : '#16a34a';
        const fillColor = isExclusion ? '#fecaca' : '#bbf7d0';

        if (zone.rayonMax > 0) {
            const circleMax = L.circle([zone.lat, zone.lon], {
                radius: zone.rayonMax * 1000,
                color: color,
                weight: 2,
                fillColor: fillColor,
                fillOpacity: 0.15,
                dashArray: isExclusion ? '5, 5' : null
            }).addTo(markersLayer);

            circleMax.bindPopup(`
                <strong>${zone.name}</strong><br>
                <span style="color: ${color}; font-weight: bold;">
                    ${isExclusion ? "Zone d'exclusion" : "Zone d'inclusion"}
                </span><br>
                Rayon: ${zone.rayonMin} - ${zone.rayonMax} km
            `);
        }

        if (zone.rayonMin > 0) {
            L.circle([zone.lat, zone.lon], {
                radius: zone.rayonMin * 1000,
                color: color,
                weight: 2,
                fillColor: '#ffffff',
                fillOpacity: 0.6,
                dashArray: '3, 3'
            }).addTo(markersLayer);
        }
    });

    const shadowUrl = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png';
    const iconConfig = { iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] };

    const blueIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
        shadowUrl, ...iconConfig
    });

    const edIcons = {
        'tres faible': L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
            shadowUrl, ...iconConfig
        }),
        'faible': L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
            shadowUrl, ...iconConfig
        }),
        'modere-': L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png',
            shadowUrl, ...iconConfig
        }),
        'modere': L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png',
            shadowUrl, ...iconConfig
        }),
        'modere+': L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
            shadowUrl, ...iconConfig
        }),
        'eleve': L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
            shadowUrl, ...iconConfig
        }),
        'tres eleve': L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl, ...iconConfig
        }),
        'extreme': L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl, ...iconConfig
        })
    };

    const markers = [];

    searchResults.slice(0, 200).forEach(city => {
        if (city.lat == null || city.lon == null || Number.isNaN(city.lat) || Number.isNaN(city.lon)) {
            debugLog('result skip invalid coords', city);
            return;
        }
        const prixAppt = city.prix_m2_appartement ? `<br>Prix appt: ${Math.round(city.prix_m2_appartement)} EUR/m2` : '';
        const prixMaison = city.prix_m2_maison ? `<br>Prix maison: ${Math.round(city.prix_m2_maison)} EUR/m2` : '';
        const edInfo = city.categorie_extreme_droite ? `<br><span style="color: ${city.couleur_extreme_droite}; font-weight: bold;">Ext. Droite: ${city.categorie_extreme_droite} (${Math.round(city.score_extreme_droite * 100)}%)</span>` : '';
        const urgenceInfo = city.distance_urgence !== null && city.distance_urgence !== undefined ? `<br><span style="color: #dc2626;">Urgence: ${city.distance_urgence} km</span>` : '';

        let icon;
        if (city.is_reference) {
            icon = blueIcon;
        } else if (city.categorie_extreme_droite && edIcons[normalizeCategoryLabel(city.categorie_extreme_droite)]) {
            icon = edIcons[normalizeCategoryLabel(city.categorie_extreme_droite)];
        } else {
            icon = blueIcon;
        }

        let popupContent;
        if (city.is_reference) {
            popupContent = `
                <strong style="color: #1f6b50;">${city.nom}</strong><br>
                <span style="display:inline-block; margin:4px 0; padding:3px 8px; border-radius:999px; background:#dceee4; color:#1f6b50; font-size:11px; font-weight:700;">
                    Ville de reference
                </span><br>
                <span style="font-size:12px; color:#2f3f37;">
                    ${city.population ? `Population: ${city.population.toLocaleString('fr-FR')}<br>` : ''}
                    ${prixAppt}
                    ${prixMaison}
                    ${edInfo}
                    ${urgenceInfo}
                </span>
            `;
        } else {
            popupContent = `
                <strong>${city.nom}</strong><br>
                <span style="font-size:12px; color:#2f3f37;">
                    Population: ${city.population.toLocaleString('fr-FR')}<br>
                    Distance: ${city.distance} km<br>
                    Proche de: ${city.ville_reference}
                    ${prixAppt}
                    ${prixMaison}
                    ${edInfo}
                    ${urgenceInfo}
                </span>
            `;
        }

        const marker = L.marker([city.lat, city.lon], { icon: icon })
            .bindPopup(popupContent)
            .addTo(markersLayer);
        markers.push(marker);
    });

    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Afficher les services d'urgence dans la zone
function displayUrgences(urgences) {
    urgencesData = urgences || [];
    const emptyDiv = document.getElementById('urgences-empty');
    const contentDiv = document.getElementById('urgences-content');
    const countSpan = document.getElementById('urgences-count');
    const tbody = document.getElementById('urgences-tbody');

    if (!urgences || urgences.length === 0) {
        if (emptyDiv) emptyDiv.classList.remove('hidden');
        if (contentDiv) contentDiv.classList.add('hidden');
        if (emptyDiv) emptyDiv.textContent = 'Aucun service d\'urgence dans la zone de recherche';
        return;
    }

    if (emptyDiv) emptyDiv.classList.add('hidden');
    if (contentDiv) contentDiv.classList.remove('hidden');
    if (countSpan) countSpan.textContent = urgences.length;

    urgences.sort((a, b) => a.distance - b.distance);

    if (tbody) {
        tbody.innerHTML = urgences.map(u => `
            <tr>
                <td>${u.nom || ''}</td>
                <td>${u.commune || ''}</td>
                <td>${u.code_postal || ''}</td>
                <td>
                    <span class="badge ${u.type === 'Public' ? 'badge--public' : 'badge--private'}">
                        ${u.type || ''}
                    </span>
                </td>
                <td class="cell-right"><span class="text-urgent">${u.distance} km</span></td>
                <td>${u.zone_reference || ''}</td>
            </tr>
        `).join('');
    }
}

function initUrgencesMap() {
    if (!urgencesMap) {
        urgencesMap = L.map('urgences-map').setView([46.5, 2.5], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(urgencesMap);
        urgencesMarkersLayer = L.layerGroup().addTo(urgencesMap);
    }
}

function updateUrgencesMap() {
    const emptyDiv = document.getElementById('urgences-map-empty');
    const contentDiv = document.getElementById('urgences-map-content');
    const countSpan = document.getElementById('urgences-map-count');

    if (!urgencesData || urgencesData.length === 0) {
        if (emptyDiv) emptyDiv.classList.remove('hidden');
        if (contentDiv) contentDiv.classList.add('hidden');
        return;
    }

    if (emptyDiv) emptyDiv.classList.add('hidden');
    if (contentDiv) contentDiv.classList.remove('hidden');
    if (countSpan) countSpan.textContent = urgencesData.length;

    initUrgencesMap();
    urgencesMarkersLayer.clearLayers();

    const bounds = [];
    const redIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
    });

    searchZones.forEach(zone => {
        if (!zone.exclure && zone.rayonMax > 0) {
            L.circle([zone.lat, zone.lon], {
                radius: zone.rayonMax * 1000,
                color: '#dc2626',
                weight: 2,
                fillColor: '#fecaca',
                fillOpacity: 0.1
            }).addTo(urgencesMarkersLayer);
        }
    });

    urgencesData.forEach(u => {
        const marker = L.marker([u.lat, u.lon], { icon: redIcon }).addTo(urgencesMarkersLayer);
        marker.bindPopup(`
            <strong>${u.nom}</strong><br>
            ${u.commune} (${u.code_postal})<br>
            Type: ${u.type}<br>
            Distance: ${u.distance} km de ${u.zone_reference}
        `);
        bounds.push([u.lat, u.lon]);
    });

    if (bounds.length > 0) {
        urgencesMap.fitBounds(bounds, { padding: [50, 50] });
    }
}

// Plein ecran pour la carte urgences
function toggleUrgencesMapFullscreen() {
    const mapView = document.getElementById('urgences-map-view');
    const fullscreenBtn = document.getElementById('urgences-fullscreen-btn');

    if (!document.fullscreenElement) {
        mapView.requestFullscreen().then(() => {
            setTimeout(() => urgencesMap.invalidateSize(), 100);
            fullscreenBtn.textContent = 'Quitter plein ecran';
        });
    } else {
        document.exitFullscreen().then(() => {
            setTimeout(() => urgencesMap.invalidateSize(), 100);
            fullscreenBtn.textContent = 'Plein ecran';
        });
    }
}

// === Tri et filtrage des resultats ===
function sortResults(columnName) {
    if (currentSort.column === columnName) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = columnName;
        currentSort.direction = 'asc';
    }

    searchResults.sort((a, b) => {
        let aVal = a[columnName];
        let bVal = b[columnName];

        if (aVal === null || aVal === undefined) aVal = '';
        if (bVal === null || bVal === undefined) bVal = '';

        if (typeof aVal === 'number' && typeof bVal === 'number') {
            return currentSort.direction === 'asc' ? aVal - bVal : bVal - aVal;
        } else {
            const compare = String(aVal).localeCompare(String(bVal), 'fr');
            return currentSort.direction === 'asc' ? compare : -compare;
        }
    });

    displayResults(searchResults);
}

function filterResults(searchTerm) {
    const term = searchTerm.toLowerCase().trim();

    if (!term) {
        displayResults(searchResults);
        const resultsInfo = document.getElementById('results-info');
        if (!resultsInfo.classList.contains('hidden')) {
            resultsInfo.querySelector('p').textContent = `${searchResults.length} resultats trouves`;
        }
        return;
    }

    const filtered = searchResults.filter(city => {
        return (
            city.nom.toLowerCase().includes(term) ||
            (city.code_postal && city.code_postal.toLowerCase().includes(term)) ||
            (city.ville_reference && city.ville_reference.toLowerCase().includes(term)) ||
            (city.population && city.population.toString().includes(term)) ||
            (city.prix_m2_appartement && city.prix_m2_appartement.toString().includes(term)) ||
            (city.prix_m2_maison && city.prix_m2_maison.toString().includes(term))
        );
    });

    displayResults(filtered);

    const resultsInfo = document.getElementById('results-info');
    if (!resultsInfo.classList.contains('hidden')) {
        resultsInfo.querySelector('p').textContent = `${filtered.length} resultats trouves (filtre sur ${searchResults.length})`;
    }
}

function clearFilter() {
    document.getElementById('results-filter').value = '';
    displayResults(searchResults);

    const resultsInfo = document.getElementById('results-info');
    if (!resultsInfo.classList.contains('hidden')) {
        resultsInfo.querySelector('p').textContent = `${searchResults.length} resultats trouves`;
    }
}

// Expose helpers for inline handlers and tests.
window.addSearchZoneData = addSearchZoneData;
window.selectAutocompleteCity = selectAutocompleteCity;
window.updateSearchZonesList = updateSearchZonesList;
window.removeSearchZone = removeSearchZone;
window.updateZoneParam = updateZoneParam;
window.sortResults = sortResults;
window.filterResults = filterResults;
window.clearFilter = clearFilter;
window.toggleUrgencesMapFullscreen = toggleUrgencesMapFullscreen;
window.applyZonesCsv = applyZonesCsv;
window.loadZonesCsv = loadZonesCsv;
window.clearZonesCsv = clearZonesCsv;
window.copyShareLink = copyShareLink;
window.openShareLink = openShareLink;

// Rechercher les villes
async function searchCities() {
    debugLog('searchCities appelee');

    // Hide share link on new search
    const shareSection = document.getElementById('share-section');
    if (shareSection) {
        shareSection.classList.add('hidden');
    }

    const inclusionZones = searchZones.filter(z => !z.exclure);
    if (inclusionZones.length === 0) {
        showError('Veuillez ajouter au moins une zone d\'inclusion');
        return;
    }

    const minPop = parseInt(document.getElementById('min-pop').value);
    const maxPop = parseInt(document.getElementById('max-pop').value);

    if (minPop >= maxPop) {
        showError('La population minimale doit etre inferieure a la population maximale');
        return;
    }

    for (const zone of searchZones) {
        if (zone.rayonMin >= zone.rayonMax) {
            showError(`Zone ${zone.name}: le rayon min doit etre inferieur au rayon max`);
            return;
        }
    }

    document.getElementById('loading').classList.remove('hidden');
    resetProgressBar();
    const infoDiv = document.getElementById('results-info');
    infoDiv.classList.add('hidden');
    infoDiv.classList.remove('alert--error');
    infoDiv.classList.add('alert--info');

    try {
        const zonesForSearch = searchZones.map(z => ({
            name: z.name,
            lat: z.lat,
            lon: z.lon,
            rayon_min: z.rayonMin,
            rayon_max: z.rayonMax,
            exclure: z.exclure
        }));

        const requestBody = {
            search_zones: zonesForSearch,
            min_population: minPop,
            max_population: maxPop
        };

        const data = await runSearch(requestBody, progress => {
            updateProgressBar(progress.processed, progress.total, progress.matched);
            infoDiv.classList.remove('hidden');
            infoDiv.querySelector('p').textContent = `... ${progress.matched || 0} villes trouvees...`;
        });

        if (data && data.results) {
            searchResults = data.results;
            displayResults(searchResults);
            updateMap();

            if (data.urgences) {
                displayUrgences(data.urgences);
                updateUrgencesMap();
            }

            document.getElementById('filter-section').classList.remove('hidden');
            infoDiv.classList.remove('hidden');
            infoDiv.querySelector('p').textContent = `OK ${searchResults.length} villes trouvees`;
        } else {
            throw new Error('Resultat vide');
        }
    } catch (error) {
        console.error('[ERROR] Erreur recherche:', error);
        showError('Erreur lors de la recherche: ' + (error.message || 'inconnue'));
        displayResults([]);
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
}

// Exporter en CSV
function exportCSV() {
    if (searchResults.length === 0) {
        alert('Aucun resultat a exporter');
        return;
    }

    const headers = ['Nom', 'Code Postal', 'Population', 'Distance (km)', 'Ville de reference', 'Prix m2 Appt', 'Prix m2 Maison', 'Score extreme droite', 'Categorie extreme droite', 'Latitude', 'Longitude'];
    const rows = searchResults.map(city => [
        city.nom,
        city.code_postal || '',
        city.population || '',
        city.distance || '',
        city.ville_reference || '',
        city.prix_m2_appartement || '',
        city.prix_m2_maison || '',
        city.score_extreme_droite || '',
        city.categorie_extreme_droite || '',
        city.lat || '',
        city.lon || ''
    ]);

    let csv = headers.join(',') + '\n';
    csv += rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'resultats_villes.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Exporter en JSON
function exportJSON() {
    if (searchResults.length === 0) {
        alert('Aucun resultat a exporter');
        return;
    }

    const parameters = {
        search_zones: searchZones.map(z => ({
            name: z.name,
            lat: z.lat,
            lon: z.lon,
            rayon_min: z.rayonMin,
            rayon_max: z.rayonMax,
            exclure: z.exclure
        })),
        min_population: parseInt(document.getElementById('min-pop').value),
        max_population: parseInt(document.getElementById('max-pop').value)
    };

    const exportData = {
        parametres: parameters,
        nombre_resultats: searchResults.length,
        date_export: new Date().toISOString(),
        resultats: searchResults
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'resultats_villes.json';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

function updateProgressBar(processed, total, matched) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    if (!progressBar || !progressText) return;

    if (!total) {
        progressBar.style.width = '0%';
        progressText.textContent = '0 villes trouvees';
        return;
    }

    const percent = Math.min((processed / total) * 100, 100);
    progressBar.style.width = percent + '%';
    progressText.textContent = `${matched || 0} villes trouvees`;
}

function resetProgressBar() {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    if (progressBar) progressBar.style.width = '0%';
    if (progressText) progressText.textContent = '0 villes trouvees';
}

// Sauvegarder les resultats
function saveResults() {
    if (searchResults.length === 0) {
        alert('Aucun resultat a sauvegarder');
        return;
    }

    const shareSection = document.getElementById('share-section');
    shareSection.classList.remove('hidden');
    shareSection.querySelector('p').textContent = 'Generation du lien...';

    const parameters = {
        v: 1,
        ts: new Date().toISOString(),
        search_zones: searchZones.map(z => ({
            name: z.name,
            lat: z.lat,
            lon: z.lon,
            rayon_min: z.rayonMin,
            rayon_max: z.rayonMax,
            exclure: z.exclure
        })),
        min_population: parseInt(document.getElementById('min-pop').value),
        max_population: parseInt(document.getElementById('max-pop').value)
    };

    const encoded = base64UrlEncode(parameters);
    const shareUrl = new URL('results.html', window.location);
    shareUrl.searchParams.set('q', encoded);

    document.getElementById('share-link-inline').value = shareUrl.toString();
    shareSection.querySelector('p').textContent = 'Lien permanent pour partager';
}

function copyShareLink() {
    const link = document.getElementById('share-link-inline');
    link.select();
    link.setSelectionRange(0, 99999);

    try {
        document.execCommand('copy');
        alert('Lien copie !');
    } catch (err) {
        navigator.clipboard.writeText(link.value).then(() => {
            alert('Lien copie !');
        }).catch(() => {
            alert('Impossible de copier le lien');
        });
    }
}

function openShareLink() {
    const link = document.getElementById('share-link-inline').value;
    if (!link) {
        alert('Lien vide');
        return;
    }
    window.open(link, '_blank');
}


