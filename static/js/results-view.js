// Variables globales
let savedData = null;
let map = null;
let markersLayer = null;
let urgencesMap = null;
let urgencesMarkersLayer = null;
let currentSort = { column: 'distance', direction: 'asc' };
let filteredResults = null;  // Pour stocker les résultats filtrés
let urgencesData = [];  // Services d'urgence de la recherche

let searchWorker = null;
let workerRequestId = 0;
const workerRequests = new Map();
let shareTag = 'partage';

function base64UrlDecode(token) {
    let base64 = token.replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4) {
        base64 += '=';
    }
    const binary = atob(base64);
    const bytes = Uint8Array.from(binary, char => char.charCodeAt(0));
    const json = new TextDecoder().decode(bytes);
    return JSON.parse(json);
}

function getSearchWorker() {
    if (searchWorker) return searchWorker;

    searchWorker = new Worker('./static/js/search-worker.js?v=20260202d');
    searchWorker.onmessage = event => {
        const data = event.data || {};
        const request = workerRequests.get(data.id);

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

function runSearch(params) {
    const worker = getSearchWorker();
    const id = workerRequestId + 1;
    workerRequestId = id;

    return new Promise((resolve, reject) => {
        workerRequests.set(id, { resolve, reject });
        worker.postMessage({ type: 'search', id, params });
    });
}


// Configuration des icônes Leaflet
const shadowUrl = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png';
const iconConfig = { iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] };

const blueIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl, ...iconConfig
});

// Icônes colorées selon score extrême droite
const edIcons = {
    'Très faible': L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        shadowUrl, ...iconConfig
    }),
    'Faible': L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        shadowUrl, ...iconConfig
    }),
    'Modéré-': L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png',
        shadowUrl, ...iconConfig
    }),
    'Modéré': L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png',
        shadowUrl, ...iconConfig
    }),
    'Modéré+': L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
        shadowUrl, ...iconConfig
    }),
    'Élevé': L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
        shadowUrl, ...iconConfig
    }),
    'Très élevé': L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl, ...iconConfig
    }),
    'Extrême': L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl, ...iconConfig
    })
};

// Charger les resultats au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    loadSharedResults();
    setupScrollTop();
    initTabs();
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

// Charger les resultats sauvegardes
// Afficher le contenu
function displayContent() {
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('content').classList.remove('hidden');

    const metadata = `${savedData.results.length} resultats - Recherche du ${formatDate(savedData.created_at)}`;
    document.getElementById('result-metadata').textContent = metadata;

    updateResultCount(savedData.results.length, null);

    displayParameters(savedData.parameters);
    displayResults(savedData.results);

    if (savedData.urgences) {
        displayUrgences(savedData.urgences);
        updateUrgencesMap();
    }

    initMap();
}

// Afficher une erreur
function showError() {
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('error').classList.remove('hidden');
}

// Formater une date ISO
function formatDate(isoDate) {
    const date = new Date(isoDate);
    return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Afficher les parametres de recherche
function displayParameters(params) {
    const container = document.getElementById('params-display');

    if (!params) {
        container.innerHTML = '<p class="muted">Parametres non disponibles</p>';
        return;
    }

    let zonesHtml = '';

    if (params.search_zones && Array.isArray(params.search_zones)) {
        const inclusionZones = params.search_zones.filter(z => !z.exclure);
        const exclusionZones = params.search_zones.filter(z => z.exclure);

        if (inclusionZones.length > 0) {
            zonesHtml += `
                <div class="param-section">
                    <p class="param-title">Zones d'inclusion</p>
                    <div class="param-chips">
                        ${inclusionZones.map(z => `
                            <div class="param-chip">${z.name} (${z.rayon_min}-${z.rayon_max} km)</div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (exclusionZones.length > 0) {
            zonesHtml += `
                <div class="param-section">
                    <p class="param-title">Zones d'exclusion</p>
                    <div class="param-chips">
                        ${exclusionZones.map(z => `
                            <div class="param-chip param-chip--exclude">${z.name} (${z.rayon_min}-${z.rayon_max} km)</div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    } else if (params.reference_cities && Array.isArray(params.reference_cities)) {
        const refCities = params.reference_cities.map(c => c.name || c);
        zonesHtml = `
            <div class="param-section">
                <p class="param-title">Villes de reference</p>
                <div class="param-chips">
                    ${refCities.map(name => `<div class="param-chip">${name}</div>`).join('')}
                </div>
            </div>
            <div class="param-section">
                <p class="param-title">Distance (km)</p>
                <p>${params.min_distance || 0} - ${params.max_distance || 200}</p>
            </div>
        `;
    }

    container.innerHTML = `
        ${zonesHtml}
        <div class="param-section">
            <p class="param-title">Population</p>
            <p>${(params.min_population || 0).toLocaleString('fr-FR')} - ${(params.max_population || 50000).toLocaleString('fr-FR')}</p>
        </div>
    `;
}

function displayResults(results) {
    const container = document.getElementById('results-list');

    if (!results || results.length === 0) {
        container.innerHTML = '<p class="muted" style="text-align:center; padding:24px;">Aucun resultat</p>';
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
        return `<th scope="col" class="sortable ${alignClass} ${extraClass}" onclick="sortResults('${column}')">${label}${indicatorHtml}</th>`;
    };

    const apptBreaks = computeBreaks('prix_m2_appartement');
    const maisonBreaks = computeBreaks('prix_m2_maison');

    let html = '<div class="table-wrap"><table class="data-table">';
    html += '<thead><tr>';
    html += sortableHeader('nom', 'Ville', 'left', 'col-name');
    html += '<th scope="col" class="cell-center">Wiki</th>';
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

function initMap() {
    if (!map) {
        map = L.map('map').setView([46.603354, 1.888334], 6);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(map);

        markersLayer = L.layerGroup().addTo(map);
    }

    updateMap();
}

// Mettre à jour la carte
function updateMap() {
    if (!map || !savedData) return;

    markersLayer.clearLayers();

    const bounds = [];

    // Dessiner les cercles et marqueurs des zones
    drawZonesOnMap(bounds);

    // Ajouter les marqueurs pour les résultats (colorés selon score extrême droite)
    const resultsToShow = savedData.results.slice(0, 200); // Limiter pour performance

    resultsToShow.forEach(city => {
        // Choisir l'icône: bleu pour les villes de référence, sinon selon le score extrême droite
        let icon;
        if (city.is_reference) {
            icon = blueIcon;
        } else if (city.categorie_extreme_droite && edIcons[city.categorie_extreme_droite]) {
            icon = edIcons[city.categorie_extreme_droite];
        } else {
            icon = blueIcon;
        }

        const marker = L.marker([city.lat, city.lon], { icon: icon }).addTo(markersLayer);

                const prixAppt = city.prix_m2_appartement ? `${city.prix_m2_appartement.toLocaleString('fr-FR')} EUR/m2` : 'N/A';
        const prixMaison = city.prix_m2_maison ? `${city.prix_m2_maison.toLocaleString('fr-FR')} EUR/m2` : 'N/A';
        const edInfo = city.categorie_extreme_droite ? `<br><span style="color: ${city.couleur_extreme_droite}; font-weight: bold;">Ext. droite: ${city.categorie_extreme_droite} (${Math.round(city.score_extreme_droite * 100)}%)</span>` : '';
        const urgenceInfo = city.distance_urgence !== null && city.distance_urgence !== undefined ? `<br><span style="color: #dc2626;">Urgence: ${city.distance_urgence} km</span>` : '';

        // Contenu du popup different pour les villes de reference
        let popupContent;
        if (city.is_reference) {
            popupContent = `
                <strong style="color: #1f6b50;">${city.nom}</strong><br>
                <span style="display:inline-block; margin:4px 0; padding:3px 8px; border-radius:999px; background:#dceee4; color:#1f6b50; font-size:11px; font-weight:700;">
                    Ville de reference
                </span><br>
                <span style="font-size:12px; color:#2f3f37;">
                    ${city.population ? `Population: ${city.population.toLocaleString('fr-FR')}<br>` : ''}
                    Prix appt: ${prixAppt}<br>
                    Prix maison: ${prixMaison}
                    ${edInfo}
                    ${urgenceInfo}
                </span>
            `;
        } else {
            popupContent = `
                <strong>${city.nom}</strong><br>
                <span style="font-size:12px; color:#2f3f37;">
                    Population: ${city.population.toLocaleString('fr-FR')}<br>
                    Distance: ${city.distance} km de ${city.ville_reference}<br>
                    Prix appt: ${prixAppt}<br>
                    Prix maison: ${prixMaison}
                    ${edInfo}
                    ${urgenceInfo}
                </span>
            `;
        }

        marker.bindPopup(popupContent);
        bounds.push([city.lat, city.lon]);
    });

    // Ajuster la vue pour montrer tous les marqueurs, sinon fallback sur la France
    if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50] });
    } else {
        map.setView([46.603354, 1.888334], 6);
    }
}

// Changer d'onglet
function initTabs() {
    const tabs = Array.from(document.querySelectorAll('.tab-button'));
    if (tabs.length === 0) return;

    tabs.forEach(tab => {
        tab.addEventListener('keydown', event => {
            if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault();

            const currentIndex = tabs.indexOf(event.currentTarget);
            let nextIndex = currentIndex;

            if (event.key === 'ArrowRight') {
                nextIndex = (currentIndex + 1) % tabs.length;
            } else if (event.key === 'ArrowLeft') {
                nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
            } else if (event.key === 'Home') {
                nextIndex = 0;
            } else if (event.key === 'End') {
                nextIndex = tabs.length - 1;
            }

            const nextTab = tabs[nextIndex];
            if (nextTab && nextTab.id) {
                const target = nextTab.id.replace('tab-', '');
                switchTab(target);
                nextTab.focus();
            }
        });
    });
}

function switchTab(tabName) {
    // Mettre a jour les boutons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
        btn.setAttribute('tabindex', '-1');
    });
    const activeBtn = document.getElementById(`tab-${tabName}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.setAttribute('aria-selected', 'true');
        activeBtn.setAttribute('tabindex', '0');
    }

    // Mettre a jour le contenu
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
        content.setAttribute('aria-hidden', 'true');
    });

    const activePanel = document.getElementById(`${tabName}-view`);
    if (activePanel) {
        activePanel.classList.remove('hidden');
        activePanel.setAttribute('aria-hidden', 'false');
    }

    if (tabName === 'map') {
        // Forcer le rafraichissement de la carte
        setTimeout(() => {
            if (map) {
                map.invalidateSize();
            }
        }, 100);
    } else if (tabName === 'urgences-map') {
        // Forcer le rafraichissement de la carte urgences
        setTimeout(() => {
            if (urgencesMap) {
                urgencesMap.invalidateSize();
            }
            updateUrgencesMap();
        }, 100);
    }
}

// Exporter en CSV

function exportResultsCSV() {
    if (!savedData) return;

    // Utiliser les résultats filtrés s'ils existent
    const resultsToExport = filteredResults || savedData.results;

    const headers = ['Nom', 'Code Postal', 'Population', 'Distance (km)', 'Ville de reference', 'Prix m2 Appt', 'Prix m2 Maison', 'Altitude (m)', 'Temperature (C)', 'Latitude', 'Longitude'];
    const rows = resultsToExport.map(city => [
        city.nom,
        city.code_postal || '',
        city.population,
        city.distance,
        city.ville_reference,
        city.prix_m2_appartement || '',
        city.prix_m2_maison || '',
        city.altitude !== null && city.altitude !== undefined ? city.altitude : '',
        city.temperature !== null && city.temperature !== undefined ? city.temperature : '',
        city.lat,
        city.lon
    ]);

    let csv = headers.join(',') + '\n';
    csv += rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resultats_${shareTag}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Exporter en JSON
function exportResultsJSON() {
    if (!savedData) return;

    const blob = new Blob([JSON.stringify(savedData, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resultats_${shareTag}.json`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// === Tri et filtrage des résultats ===

function sortResults(columnName) {
    if (!savedData) return;

    // Basculer la direction si on clique sur la même colonne
    if (currentSort.column === columnName) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = columnName;
        currentSort.direction = 'asc';
    }

    // Utiliser les résultats filtrés s'ils existent, sinon les résultats complets
    const resultsToSort = filteredResults || savedData.results;

    // Trier le tableau de résultats
    resultsToSort.sort((a, b) => {
        let aVal = a[columnName];
        let bVal = b[columnName];

        // Gérer les valeurs nulles/undefined
        if (aVal === null || aVal === undefined) aVal = '';
        if (bVal === null || bVal === undefined) bVal = '';

        // Tri numérique ou alphabétique
        if (typeof aVal === 'number' && typeof bVal === 'number') {
            return currentSort.direction === 'asc' ? aVal - bVal : bVal - aVal;
        } else {
            const compare = String(aVal).localeCompare(String(bVal), 'fr');
            return currentSort.direction === 'asc' ? compare : -compare;
        }
    });

    // Réafficher les résultats triés
    displayResults(resultsToSort);
    updateMapWithResults(resultsToSort);
}

function filterResults(searchTerm) {
    if (!savedData) return;

    const term = searchTerm.toLowerCase().trim();

    if (!term) {
        filteredResults = null;
        displayResults(savedData.results);
        updateMapWithResults(savedData.results);
        // Remettre le compteur normal
        updateResultCount(savedData.results.length, null);
        return;
    }

    // Filtrer les résultats
    const filtered = savedData.results.filter(city => {
        return (
            city.nom.toLowerCase().includes(term) ||
            (city.code_postal && city.code_postal.toLowerCase().includes(term)) ||
            (city.ville_reference && city.ville_reference.toLowerCase().includes(term)) ||
            (city.population && city.population.toString().includes(term)) ||
            (city.prix_m2_appartement && city.prix_m2_appartement.toString().includes(term)) ||
            (city.prix_m2_maison && city.prix_m2_maison.toString().includes(term))
        );
    });

    filteredResults = filtered;
    displayResults(filtered);
    updateMapWithResults(filtered);
    updateResultCount(filtered.length, savedData.results.length);
}

function clearFilter() {
    document.getElementById('results-filter').value = '';
    filteredResults = null;
    displayResults(savedData.results);
    updateMapWithResults(savedData.results);
    updateResultCount(savedData.results.length, null);
}

function updateResultCount(count, total) {
    const countElement = document.getElementById('result-count');
    if (countElement) {
        if (total !== null) {
            countElement.textContent = `${count} résultats (filtré sur ${total})`;
        } else {
            countElement.textContent = `${count} résultats`;
        }
    }
}

// Dessiner les zones (cercles) sur la carte
function drawZonesOnMap(bounds) {
    const params = savedData?.parameters;
    if (!params) return;

    // Support nouvelle structure (search_zones) et ancienne (reference_cities)
    let zones = [];

    if (params.search_zones && Array.isArray(params.search_zones)) {
        zones = params.search_zones;
    } else if (params.reference_cities && Array.isArray(params.reference_cities)) {
        zones = params.reference_cities.map(c => ({
            name: c.name,
            lat: c.lat,
            lon: c.lon,
            rayon_min: params.min_distance || 0,
            rayon_max: params.max_distance || 200,
            exclure: false
        }));
    }

    zones.forEach(zone => {
        const isExclusion = zone.exclure;
        const color = isExclusion ? '#dc2626' : '#16a34a';
        const fillColor = isExclusion ? '#fecaca' : '#bbf7d0';

        // Cercle pour le rayon max
        if (zone.rayon_max > 0) {
            const circleMax = L.circle([zone.lat, zone.lon], {
                radius: zone.rayon_max * 1000,
                color: color,
                weight: 2,
                fillColor: fillColor,
                fillOpacity: 0.15,
                dashArray: isExclusion ? '5, 5' : null
            }).addTo(markersLayer);

            circleMax.bindPopup(`
                <strong>${zone.name}</strong><br>
                <span style="color: ${color}; font-weight: bold;">
                    ${isExclusion ? 'Zone d\'exclusion' : 'Zone d\'inclusion'}
                </span><br>
                Rayon: ${zone.rayon_min} - ${zone.rayon_max} km
            `);
        }

        // Cercle pour le rayon min
        if (zone.rayon_min > 0) {
            L.circle([zone.lat, zone.lon], {
                radius: zone.rayon_min * 1000,
                color: color,
                weight: 2,
                fillColor: '#ffffff',
                fillOpacity: 0.6,
                dashArray: '3, 3'
            }).addTo(markersLayer);
        }

        bounds.push([zone.lat, zone.lon]);
    });
}

function updateMapWithResults(results) {
    if (!map) return;

    markersLayer.clearLayers();
    const bounds = [];

    // Dessiner les zones (cercles)
    drawZonesOnMap(bounds);

    // Ajouter les marqueurs pour les résultats filtrés (colorés selon score extrême droite)
    const resultsToShow = results.slice(0, 200); // Limiter pour performance

    resultsToShow.forEach(city => {
        // Choisir l'icône: bleu pour les villes de référence, sinon selon le score extrême droite
        let icon;
        if (city.is_reference) {
            icon = blueIcon;
        } else if (city.categorie_extreme_droite && edIcons[city.categorie_extreme_droite]) {
            icon = edIcons[city.categorie_extreme_droite];
        } else {
            icon = blueIcon;
        }

        const marker = L.marker([city.lat, city.lon], { icon: icon }).addTo(markersLayer);

                const prixAppt = city.prix_m2_appartement ? `${city.prix_m2_appartement.toLocaleString('fr-FR')} EUR/m2` : 'N/A';
        const prixMaison = city.prix_m2_maison ? `${city.prix_m2_maison.toLocaleString('fr-FR')} EUR/m2` : 'N/A';
        const edInfo = city.categorie_extreme_droite ? `<br><span style="color: ${city.couleur_extreme_droite}; font-weight: bold;">Ext. droite: ${city.categorie_extreme_droite} (${Math.round(city.score_extreme_droite * 100)}%)</span>` : '';
        const urgenceInfo = city.distance_urgence !== null && city.distance_urgence !== undefined ? `<br><span style="color: #dc2626;">Urgence: ${city.distance_urgence} km</span>` : '';

        // Contenu du popup different pour les villes de reference
        let popupContent;
        if (city.is_reference) {
            popupContent = `
                <strong style="color: #1f6b50;">${city.nom}</strong><br>
                <span style="display:inline-block; margin:4px 0; padding:3px 8px; border-radius:999px; background:#dceee4; color:#1f6b50; font-size:11px; font-weight:700;">
                    Ville de reference
                </span><br>
                <span style="font-size:12px; color:#2f3f37;">
                    ${city.population ? `Population: ${city.population.toLocaleString('fr-FR')}<br>` : ''}
                    Prix appt: ${prixAppt}<br>
                    Prix maison: ${prixMaison}
                    ${edInfo}
                    ${urgenceInfo}
                </span>
            `;
        } else {
            popupContent = `
                <strong>${city.nom}</strong><br>
                <span style="font-size:12px; color:#2f3f37;">
                    Population: ${city.population.toLocaleString('fr-FR')}<br>
                    Distance: ${city.distance} km de ${city.ville_reference}<br>
                    Prix appt: ${prixAppt}<br>
                    Prix maison: ${prixMaison}
                    ${edInfo}
                    ${urgenceInfo}
                </span>
            `;
        }

        marker.bindPopup(popupContent);
        bounds.push([city.lat, city.lon]);
    });

    // Ajuster la vue pour montrer tous les marqueurs
    if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50] });
    } else {
        map.setView([46.603354, 1.888334], 6);
    }
}

// Mode plein écran pour la carte
function toggleMapFullscreen() {
    const mapView = document.getElementById('map-view');
    const mapContainer = document.getElementById('map');
    const fullscreenBtn = document.getElementById('fullscreen-btn');

    if (!document.fullscreenElement) {
        mapView.requestFullscreen().then(() => {
            // Attendre un peu pour que le plein écran s'active
            setTimeout(() => {
                map.invalidateSize();
                // Réajuster le zoom après le passage en plein écran
                if (savedData) {
                    const resultsToShow = filteredResults || savedData.results;
                    updateMapWithResults(resultsToShow);
                }
            }, 100);
            fullscreenBtn.textContent = 'Quitter plein ecran';
        });
    } else {
        document.exitFullscreen().then(() => {
            setTimeout(() => {
                map.invalidateSize();
            }, 100);
            fullscreenBtn.textContent = 'Plein ecran';
        });
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
        if (emptyDiv) emptyDiv.textContent = 'Aucun service d\'urgence enregistre pour cette recherche';
        return;
    }

    if (emptyDiv) emptyDiv.classList.add('hidden');
    if (contentDiv) contentDiv.classList.remove('hidden');
    if (countSpan) countSpan.textContent = urgences.length;

    // Trier par distance
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

// Initialiser la carte des urgences
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

// Mettre à jour la carte des urgences
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

    // Icône rouge pour les urgences
    const redIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
    });

    // Dessiner les zones de recherche (cercles) depuis les paramètres sauvegardés
    if (savedData && savedData.parameters && savedData.parameters.search_zones) {
        savedData.parameters.search_zones.forEach(zone => {
            if (!zone.exclure && zone.rayon_max > 0) {
                L.circle([zone.lat, zone.lon], {
                    radius: zone.rayon_max * 1000,
                    color: '#dc2626',
                    weight: 2,
                    fillColor: '#fecaca',
                    fillOpacity: 0.1
                }).addTo(urgencesMarkersLayer);
            }
        });
    }

    // Ajouter les marqueurs des urgences
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

// Plein écran pour la carte urgences
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

// Charger les resultats depuis l'URL partagee
async function loadSharedResults() {
    const token = new URLSearchParams(window.location.search).get('q');

    if (!token) {
        showError();
        return;
    }

    let params;
    try {
        params = base64UrlDecode(token);
    } catch (error) {
        console.error('Erreur decodage:', error);
        showError();
        return;
    }

    if (!params || !Array.isArray(params.search_zones)) {
        showError();
        return;
    }

    shareTag = params.ts ? params.ts.replace(/[:.]/g, '-') : 'partage';

    try {
        const data = await runSearch({
            search_zones: params.search_zones,
            min_population: params.min_population,
            max_population: params.max_population
        });

        savedData = {
            created_at: params.ts || new Date().toISOString(),
            parameters: {
                search_zones: params.search_zones,
                min_population: params.min_population,
                max_population: params.max_population,
                fetch_altitude: true,
                fetch_temperature: true
            },
            results: data.results || [],
            urgences: data.urgences || []
        };

        displayContent();
    } catch (error) {
        console.error('Erreur chargement:', error);
        showError();
    }
}


