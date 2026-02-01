import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
import unicodedata


def normalize_name(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", str(value))
    without_accents = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return without_accents.upper().strip()


def to_float(value):
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def to_int(value):
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def normalize_code_postal(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return ""
    try:
        num = int(float(text))
        return f"{num:05d}"
    except ValueError:
        return text


def read_communes(communes_csv: Path):
    communes = []
    index = []

    with communes_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            code_insee = (row.get("code_insee") or "").strip()
            nom = (row.get("nom") or "").strip()

            commune = {
                "code_insee": code_insee,
                "nom": nom,
                "code_postal": normalize_code_postal(row.get("code_postal")),
                "departement": (row.get("departement") or "").strip(),
                "region": (row.get("region") or "").strip(),
                "latitude": to_float(row.get("latitude")),
                "longitude": to_float(row.get("longitude")),
                "population": to_int(row.get("population")),
                "altitude": to_float(row.get("altitude")),
                "temperature": to_float(row.get("temperature")),
                "prix_m2_appartement": to_float(row.get("prix_m2_appartement")),
                "prix_m2_maison": to_float(row.get("prix_m2_maison")),
                "score_extreme_droite": to_float(row.get("score_extreme_droite")),
                "wikipedia_url": (row.get("wikipedia_url") or "").strip() or None,
                "urgence_distance": to_float(row.get("urgence_distance")),
                "urgence_nom": (row.get("urgence_nom") or "").strip() or None,
                "urgence_commune": (row.get("urgence_commune") or "").strip() or None,
                "urgence_type": (row.get("urgence_type") or "").strip() or None,
            }
            communes.append(commune)

            normalized = normalize_name(nom)
            index.append({
                "name": nom,
                "normalized": normalized,
                "code_insee": code_insee,
                "code_postal": commune["code_postal"],
                "lat": commune["latitude"],
                "lon": commune["longitude"],
                "population": commune["population"],
            })

    return communes, index


def read_urgences(urgences_csv: Path):
    urgences = []

    with urgences_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            urgences.append({
                "finess": (row.get("FINESS_Etab") or "").strip(),
                "nom": (row.get("Nom_court") or "").strip(),
                "code_postal": normalize_code_postal(row.get("Code_postal")),
                "commune": (row.get("Commune") or "").strip(),
                "type": (row.get("Public_ou_prive") or "").strip(),
                "lat": to_float(row.get("Lat")),
                "lon": to_float(row.get("Long")),
            })

    return urgences


def write_json(path: Path, payload):
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="Build JSON assets for the static app.")
    parser.add_argument("--data-dir", default=None, help="Directory containing CSV files")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    data_dir = Path(args.data_dir) if args.data_dir else base_dir / "data"

    communes_csv = data_dir / "communes_enrichies.csv"
    urgences_csv = data_dir / "urgences_service_public.csv"

    if not communes_csv.exists():
        raise SystemExit(f"Missing {communes_csv}")
    if not urgences_csv.exists():
        raise SystemExit(f"Missing {urgences_csv}")

    communes, index = read_communes(communes_csv)
    urgences = read_urgences(urgences_csv)

    write_json(data_dir / "communes_enrichies.json", communes)
    write_json(data_dir / "communes_index.json", index)
    write_json(data_dir / "urgences_service_public.json", urgences)

    meta = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_communes": len(communes),
        "total_urgences": len(urgences),
    }
    write_json(data_dir / "meta.json", meta)

    print(f"Wrote {len(communes)} communes, {len(index)} index entries, {len(urgences)} urgences")


if __name__ == "__main__":
    main()
