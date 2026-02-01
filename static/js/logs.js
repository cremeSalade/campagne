// Fonctions pour les logs en mode statique

function startLogPolling() {
    const logsPanel = document.getElementById('logs-panel');
    const logsContent = document.getElementById('logs-content');

    if (logsPanel) {
        logsPanel.open = true;
    }

    if (logsContent) {
        logsContent.innerHTML = '<div class="log-entry pb-2 mb-2 border-b border-gray-700">Mode statique : pas de logs serveur.</div>';
    }
}

function stopLogPolling() {
    // No-op in static mode
}

function getGeoOptions() {
    return {
        fetch_altitude: true,
        fetch_temperature: true
    };
}

function formatAltitude(alt) {
    if (alt === null || alt === undefined) return '-';
    return `${Math.round(alt)}m`;
}

function formatTemperature(temp) {
    if (temp === null || temp === undefined) return '-';
    return `${temp}°C`;
}
