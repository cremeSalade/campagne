import csv
import json
from pathlib import Path


def load_coords_from_simple_csv(path: Path):
    coords = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            code = (row.get("CODE_COMMUNE") or "").strip()
            lat = row.get("LATITUDE")
            lon = row.get("LONGITUDE")
            if not code or lat in (None, "") or lon in (None, ""):
                continue
            try:
                lat_f = float(str(lat).replace(",", "."))
                lon_f = float(str(lon).replace(",", "."))
            except ValueError:
                continue
            coords[code] = (lat_f, lon_f)
    return coords


def load_coords_from_communes_france(path: Path, wanted_codes):
    coords = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            code = (row.get("code_insee") or "").strip()
            if code not in wanted_codes:
                continue
            lat = row.get("latitude_centre") or row.get("latitude_mairie")
            lon = row.get("longitude_centre") or row.get("longitude_mairie")
            if not lat or not lon:
                continue
            try:
                lat_f = float(str(lat).replace(",", "."))
                lon_f = float(str(lon).replace(",", "."))
            except ValueError:
                continue
            coords[code] = (lat_f, lon_f)
    return coords


def main():
    static_root = Path(__file__).resolve().parents[1]
    data_dir = static_root / "data"

    communes_path = data_dir / "communes_enrichies.json"
    index_path = data_dir / "communes_index.json"

    if not communes_path.exists() or not index_path.exists():
        raise SystemExit("Missing communes_enrichies.json or communes_index.json in data/")

    # Source CSV paths (from the original app folder)
    app_root = static_root.parent / "campagne_app"
    coords_csv = app_root / "code_commune_nom_commune_latitude_longitude.csv"
    communes_fr_csv = app_root / "communes-france-2025.csv"

    if not coords_csv.exists():
        raise SystemExit(f"Missing source coords CSV: {coords_csv}")
    if not communes_fr_csv.exists():
        raise SystemExit(f"Missing communes-france-2025.csv: {communes_fr_csv}")

    communes = json.loads(communes_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))

    missing_codes = {
        c.get("code_insee")
        for c in communes
        if c.get("latitude") is None or c.get("longitude") is None
    }

    if not missing_codes:
        print("No missing coordinates detected.")
        return

    coords = load_coords_from_simple_csv(coords_csv)

    fixed_communes = 0
    for c in communes:
        if c.get("latitude") is None or c.get("longitude") is None:
            code = (c.get("code_insee") or "").strip()
            if code in coords:
                lat, lon = coords[code]
                c["latitude"] = lat
                c["longitude"] = lon
                fixed_communes += 1

    # Update index
    fixed_index = 0
    for c in index:
        if c.get("lat") is None or c.get("lon") is None:
            code = (c.get("code_insee") or "").strip()
            if code in coords:
                lat, lon = coords[code]
                c["lat"] = lat
                c["lon"] = lon
                fixed_index += 1

    # Check remaining missing and fallback to communes-france if needed
    remaining_codes = {
        c.get("code_insee")
        for c in communes
        if c.get("latitude") is None or c.get("longitude") is None
    }

    if remaining_codes:
        fallback_coords = load_coords_from_communes_france(communes_fr_csv, remaining_codes)
        for c in communes:
            if c.get("latitude") is None or c.get("longitude") is None:
                code = (c.get("code_insee") or "").strip()
                if code in fallback_coords:
                    lat, lon = fallback_coords[code]
                    c["latitude"] = lat
                    c["longitude"] = lon
                    fixed_communes += 1

        for c in index:
            if c.get("lat") is None or c.get("lon") is None:
                code = (c.get("code_insee") or "").strip()
                if code in fallback_coords:
                    lat, lon = fallback_coords[code]
                    c["lat"] = lat
                    c["lon"] = lon
                    fixed_index += 1

    communes_path.write_text(json.dumps(communes, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    index_path.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    remaining = [
        c for c in communes
        if c.get("latitude") is None or c.get("longitude") is None
    ]

    print(f"Fixed communes: {fixed_communes}")
    print(f"Fixed index: {fixed_index}")
    print(f"Remaining missing: {len(remaining)}")


if __name__ == "__main__":
    main()
