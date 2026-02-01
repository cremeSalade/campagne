let communes = null;
let urgences = null;
let communesByName = null;
let loadingPromise = null;

function normalizeName(value) {
    if (!value) return "";
    return value
        .toString()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toUpperCase()
        .trim();
}

function roundTo(value, decimals) {
    if (value === null || value === undefined) return null;
    const factor = Math.pow(10, decimals);
    return Math.round(value * factor) / factor;
}

function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
            Math.cos((lat2 * Math.PI) / 180) *
            Math.sin(dLon / 2) *
            Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function getExtremeDroiteCategory(score) {
    if (score === null || score === undefined) {
        return { label: null, color: null };
    }
    if (score < 0.15) {
        return { label: "Très faible", color: "#1e8449" };
    }
    if (score < 0.22) {
        return { label: "Faible", color: "#27ae60" };
    }
    if (score < 0.28) {
        return { label: "Modéré-", color: "#82e0aa" };
    }
    if (score < 0.33) {
        return { label: "Modéré", color: "#f4d03f" };
    }
    if (score < 0.38) {
        return { label: "Modéré+", color: "#f39c12" };
    }
    if (score < 0.43) {
        return { label: "Élevé", color: "#e67e22" };
    }
    if (score < 0.5) {
        return { label: "Très élevé", color: "#d35400" };
    }
    return { label: "Extrême", color: "#c0392b" };
}

async function loadData() {
    if (loadingPromise) return loadingPromise;

    loadingPromise = (async () => {
        const baseUrl = new URL("../../", self.location);
        const communesUrl = new URL("data/communes_enrichies.json", baseUrl);
        const urgencesUrl = new URL("data/urgences_service_public.json", baseUrl);

        const [communesRes, urgencesRes] = await Promise.all([
            fetch(communesUrl),
            fetch(urgencesUrl),
        ]);

        if (!communesRes.ok) {
            throw new Error("Impossible de charger communes_enrichies.json");
        }
        if (!urgencesRes.ok) {
            throw new Error("Impossible de charger urgences_service_public.json");
        }

        communes = await communesRes.json();
        urgences = await urgencesRes.json();

        communesByName = new Map();
        for (const commune of communes) {
            const key = normalizeName(commune.nom);
            if (!key) continue;
            const existing = communesByName.get(key);
            if (!existing || (commune.population || 0) > (existing.population || 0)) {
                communesByName.set(key, commune);
            }
        }
    })();

    return loadingPromise;
}

function buildResult(commune, distance, closestCity, isReference) {
    const category = getExtremeDroiteCategory(commune.score_extreme_droite);
    return {
        nom: commune.nom,
        code: commune.code_insee,
        population: commune.population || 0,
        distance: roundTo(distance, 1) ?? 0,
        code_postal: commune.code_postal || "",
        ville_reference: closestCity,
        lat: commune.latitude,
        lon: commune.longitude,
        prix_m2_appartement: commune.prix_m2_appartement ?? null,
        prix_m2_maison: commune.prix_m2_maison ?? null,
        altitude: commune.altitude ?? null,
        temperature: commune.temperature ?? null,
        wikipedia_url: commune.wikipedia_url || null,
        score_extreme_droite: commune.score_extreme_droite !== null && commune.score_extreme_droite !== undefined
            ? roundTo(commune.score_extreme_droite, 3)
            : null,
        categorie_extreme_droite: category.label,
        couleur_extreme_droite: category.color,
        is_reference: !!isReference,
        urgence_proche: commune.urgence_nom || null,
        distance_urgence: commune.urgence_distance ?? null,
        urgence_commune: commune.urgence_commune || null,
        urgence_type: commune.urgence_type || null,
    };
}

function getUrgencesInZones(searchZones) {
    if (!urgences || urgences.length === 0) return [];

    const inclusionZones = searchZones.filter((z) => !z.exclure);
    const urgencesInZone = [];
    const seen = new Set();

    for (const urgence of urgences) {
        if (!urgence || urgence.lat === null || urgence.lon === null) continue;
        const uLat = urgence.lat;
        const uLon = urgence.lon;
        const finess = urgence.finess || "";

        for (const zone of inclusionZones) {
            if (zone.lat === null || zone.lon === null) continue;
            const distance = haversineDistance(zone.lat, zone.lon, uLat, uLon);
            const min = zone.rayon_min ?? 0;
            const max = zone.rayon_max ?? 100;

            if (distance >= min && distance <= max && !seen.has(finess)) {
                seen.add(finess);
                urgencesInZone.push({
                    finess,
                    nom: urgence.nom || "",
                    commune: urgence.commune || "",
                    code_postal: urgence.code_postal || "",
                    type: urgence.type || "",
                    lat: uLat,
                    lon: uLon,
                    distance: roundTo(distance, 1),
                    zone_reference: zone.name || "",
                });
                break;
            }
        }
    }

    return urgencesInZone;
}

async function handleSearch(id, params) {
    await loadData();

    const zones = params.search_zones || [];
    const minPop = params.min_population ?? 0;
    const maxPop = params.max_population ?? 50000;

    const inclusionZones = zones.filter((z) => !z.exclure);
    const exclusionZones = zones.filter((z) => z.exclure);

    const resultsByCode = new Map();
    let processed = 0;
    let matched = 0;

    for (const commune of communes) {
        processed += 1;

        if (processed % 1000 === 0) {
            self.postMessage({
                type: "progress",
                id,
                processed,
                total: communes.length,
                matched,
            });
        }

        const population = commune.population || 0;
        if (population < minPop || population > maxPop) continue;
        if (commune.latitude === null || commune.longitude === null) continue;

        let inInclusion = false;
        let closestCity = "";
        let minDistance = Infinity;

        for (const zone of inclusionZones) {
            if (zone.lat === null || zone.lon === null) continue;
            const distance = haversineDistance(zone.lat, zone.lon, commune.latitude, commune.longitude);
            const min = zone.rayon_min ?? 0;
            const max = zone.rayon_max ?? 100;
            if (distance >= min && distance <= max) {
                inInclusion = true;
                if (distance < minDistance) {
                    minDistance = distance;
                    closestCity = zone.name || "";
                }
            }
        }

        if (!inInclusion) continue;

        let inExclusion = false;
        for (const zone of exclusionZones) {
            if (zone.lat === null || zone.lon === null) continue;
            const distance = haversineDistance(zone.lat, zone.lon, commune.latitude, commune.longitude);
            const min = zone.rayon_min ?? 0;
            const max = zone.rayon_max ?? 100;
            if (distance >= min && distance <= max) {
                inExclusion = true;
                break;
            }
        }

        if (inExclusion) continue;

        const code = commune.code_insee || commune.nom;
        const existing = resultsByCode.get(code);
        if (!existing || (minDistance < existing.distance)) {
            resultsByCode.set(code, buildResult(commune, minDistance, closestCity, false));
            matched += 1;
        }
    }

    for (const zone of inclusionZones) {
        const zoneName = zone.name || "";
        const commune = communesByName.get(normalizeName(zoneName));
        if (commune) {
            const refResult = buildResult(commune, 0, "Ville de référence", true);
            const key = commune.code_insee || `ref_${zoneName}`;
            resultsByCode.set(key, refResult);
        } else {
            resultsByCode.set(`ref_${zoneName}`, {
                nom: zoneName,
                code: "",
                population: 0,
                distance: 0,
                code_postal: "",
                ville_reference: "Ville de référence",
                lat: zone.lat,
                lon: zone.lon,
                prix_m2_appartement: null,
                prix_m2_maison: null,
                altitude: null,
                temperature: null,
                wikipedia_url: null,
                score_extreme_droite: null,
                categorie_extreme_droite: null,
                couleur_extreme_droite: null,
                is_reference: true,
                urgence_proche: null,
                distance_urgence: null,
                urgence_commune: null,
                urgence_type: null,
            });
        }
    }

    const sorted = Array.from(resultsByCode.values()).sort((a, b) => a.distance - b.distance);
    const limited = sorted.slice(0, 500);

    const urgencesInZone = getUrgencesInZones(zones);

    self.postMessage({
        type: "result",
        id,
        results: limited,
        urgences: urgencesInZone,
        total: communes.length,
    });
}

self.onmessage = (event) => {
    const { type, id, params } = event.data || {};

    if (type === "init") {
        loadData()
            .then(() => self.postMessage({ type: "ready" }))
            .catch((error) => self.postMessage({ type: "error", id, message: error.message }));
        return;
    }

    if (type === "search") {
        handleSearch(id, params).catch((error) => {
            self.postMessage({ type: "error", id, message: error.message || "Erreur inconnue" });
        });
    }
};
