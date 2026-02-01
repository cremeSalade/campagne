from pathlib import Path
import json
import math
import base64
import unicodedata

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def normalize_name(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", str(value))
    without_accents = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return without_accents.upper().strip()


def haversine_distance(lat1, lon1, lat2, lon2):
    r = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def base64url_encode(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    token = base64.urlsafe_b64encode(raw).decode("utf-8")
    return token.rstrip("=")


def base64url_decode(token: str) -> dict:
    padding = "=" * ((4 - len(token) % 4) % 4)
    raw = base64.urlsafe_b64decode(token + padding)
    return json.loads(raw.decode("utf-8"))


def find_city_with_coords(index, name="Paris"):
    target_norm = normalize_name(name)
    candidates = [city for city in index if city.get("normalized") == target_norm]
    candidates.sort(key=lambda c: c.get("population") or 0, reverse=True)

    for city in candidates:
        if city.get("lat") is not None and city.get("lon") is not None:
            return city

    for city in index:
        if city.get("lat") is not None and city.get("lon") is not None:
            return city

    return None


def main():
    communes_path = DATA_DIR / "communes_enrichies.json"
    index_path = DATA_DIR / "communes_index.json"
    urgences_path = DATA_DIR / "urgences_service_public.json"

    if not communes_path.exists():
        raise SystemExit(f"Missing {communes_path}")
    if not index_path.exists():
        raise SystemExit(f"Missing {index_path}")
    if not urgences_path.exists():
        raise SystemExit(f"Missing {urgences_path}")

    communes = json.loads(communes_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    urgences = json.loads(urgences_path.read_text(encoding="utf-8"))

    assert len(communes) > 10000, "Dataset communes trop petit"
    assert len(index) == len(communes), "Index autocomplete incohérent"
    assert len(urgences) > 100, "Dataset urgences trop petit"

    sample = communes[0]
    for key in ["nom", "latitude", "longitude", "population"]:
        assert key in sample, f"Champ manquant: {key}"

    target = find_city_with_coords(index)
    assert target is not None, "Aucune ville avec coordonnées valides"

    zone_lat = target.get("lat")
    zone_lon = target.get("lon")
    assert zone_lat is not None and zone_lon is not None, "Coordonnées invalides"

    results = []
    for commune in communes:
        pop = commune.get("population") or 0
        if pop < 5000 or pop > 50000:
            continue
        lat = commune.get("latitude")
        lon = commune.get("longitude")
        if lat is None or lon is None:
            continue
        distance = haversine_distance(zone_lat, zone_lon, lat, lon)
        if distance <= 50:
            results.append(commune)

    assert len(results) > 0, "Recherche locale ne renvoie aucun résultat"

    urgences_in_zone = []
    for urgence in urgences:
        lat = urgence.get("lat")
        lon = urgence.get("lon")
        if lat is None or lon is None:
            continue
        distance = haversine_distance(zone_lat, zone_lon, lat, lon)
        if distance <= 50:
            urgences_in_zone.append(urgence)

    assert urgences_in_zone is not None, "Erreur calcul urgences"

    payload = {
        "v": 1,
        "ts": "2026-02-01T00:00:00Z",
        "search_zones": [{
            "name": target.get("name"),
            "lat": zone_lat,
            "lon": zone_lon,
            "rayon_min": 0,
            "rayon_max": 50,
            "exclure": False,
        }],
        "min_population": 5000,
        "max_population": 50000,
    }

    token = base64url_encode(payload)
    decoded = base64url_decode(token)
    assert decoded["v"] == payload["v"], "Encodage base64url invalide"

    print("OK - tests statiques passés")


if __name__ == "__main__":
    main()
