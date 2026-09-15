import requests

METASTORE_URL = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items"
THEME = "Hospitals"

def get_hospital_data_sets():
    resp = requests.get(METASTORE_URL, timeout=60)
    resp.raise_for_status()
    items = resp.json()
    hospitals = [d for d in items if THEME in d.get("theme", [])]
    return hospitals

def main():
    data_sets = get_hospital_data_sets()
    print(data_sets)

if __name__ == "__main__":
    main()