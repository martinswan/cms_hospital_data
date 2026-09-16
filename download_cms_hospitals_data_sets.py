import requests
import json
from pathlib import Path
import re
import io
import pandas as pd

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

def process_data_set(data_set):
    # download the files, rename the headers, and save.
    result = {
        "identifier": data_set["identifier"],
        "title": data_set.get("title"),
        "modified": data_set["modified"],
        "file_name": None,
        "success": False,
        "error": None,
    }
    try:
        url = get_csv_url(data_set)

        file_name = url.split("/")[-1]
        result["file_name"] = file_name

        resp = requests.get(url, timeout=120)
        resp.raise_for_status()

        df = pd.read_csv(
            io.BytesIO(resp.content),
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        df.columns = [to_snake_case(c) for c in df.columns]
        df.to_csv(OUTPUT_DIR / file_name, index=False)

        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result

def main():
    data_sets = get_hospital_data_sets()
    state = load_state()
    process_list = build_process_list(data_sets, state)

    print(f"{len(data_sets)} data sets")
    print(f"{len(process_list)} to process")

    OUTPUT_DIR.mkdir(exist_ok=True)

    if process_list:
        result = process_data_set(process_list[0])
        print(result)

if __name__ == "__main__":
    main()