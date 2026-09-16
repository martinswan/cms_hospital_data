import io
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

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

MAX_WORKERS = 6 

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

def save_state(state):
    # Write to a temp file first, then swap it in, so a crash mid-write
    # can't leave a half-written state.json behind.
    tmp_file = STATE_FILE.with_suffix(".json.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp_file.replace(STATE_FILE)

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

    succeeded = 0
    failed = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_data_set, d) for d in process_list]

        # Results arrive as each download finishes. Only this main thread
        # updates and saves state.
        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                state[result["identifier"]] = {
                    "title": result["title"],
                    "modified": result["modified"],
                    "file_name": result["file_name"],
                    "last_processed_at": datetime.now(timezone.utc).isoformat(),
                }
                save_state(state)
                succeeded += 1
                print(f"  OK    {result['identifier']}  {result['file_name']}")
            else:
                failed.append(result)
                print(f"  FAIL  {result['identifier']}  {result['error']}")

    # --- Summary ---
    skipped = len(data_sets) - len(process_list)
    print(f"Done: {succeeded} succeeded, {len(failed)} failed, {skipped} skipped")

if __name__ == "__main__":
    main()