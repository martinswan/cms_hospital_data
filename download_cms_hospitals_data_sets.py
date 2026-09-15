import requests
import json
from pathlib import Path

METASTORE_URL = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items"
THEME = "Hospitals"

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state.json"

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

def main():
    data_sets = get_hospital_data_sets()
    state = load_state()
    process_list = build_process_list(data_sets, state)

    print(f"{len(data_sets)} data sets")
    print(f"{len(process_list)} to process")

if __name__ == "__main__":
    main()