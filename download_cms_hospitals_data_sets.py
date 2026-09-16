import requests
import json
from pathlib import Path
import re

METASTORE_URL = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items"
THEME = "Hospitals"

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state.json"
OUTPUT_DIR = BASE_DIR / "output"

HEADER_REPLACEMENTS = {
    "'": "",
    "’": "",
    "&": "_and_",
    "%": "_percent_",
    "#": "_num_",
}

def get_hospital_data_sets():
    resp = requests.get(METASTORE_URL, timeout=60)
    resp.raise_for_status()
    items = resp.json()
    # Each item in the metastore has a them. we just want the items where the theme includes THEME.
    hospitals = [d for d in items if THEME in d.get("theme", [])]
    return hospitals

def load_state():
    # State shows where we are at with downloading the files.
    # If the state file doesn't exist yet then return an empty dict.
    if not STATE_FILE.exists():
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def build_process_list(data_sets, state):
    process_list = []
    for d in data_sets:
        identifier = d["identifier"]
        previous = state.get(identifier)
        # New dataset, or its modified date changed since we last processed it
        if previous is None or previous["modified"] != d["modified"]:
            process_list.append(d)
    return process_list

def get_csv_url(data_set):
    for dist in data_set.get("distribution", []):
        if dist.get("mediaType") == "text/csv":
            return dist.get("downloadURL")
    return None

def to_snake_case(name, replacements=HEADER_REPLACEMENTS):
    for old, new in replacements.items():
        name = name.replace(old, new)
    name = name.lower()
    # Any run of characters that isn't a lowercase letter or digit becomes a single underscore
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")

def main():
    data_sets = get_hospital_data_sets()
    state = load_state()
    process_list = build_process_list(data_sets, state)

    print(f"{len(data_sets)} data sets")
    print(f"{len(process_list)} to process")

    for d in process_list:
        print(f"  {d['identifier']}  {d['modified']}  {get_csv_url(d)}")

if __name__ == "__main__":
    main()