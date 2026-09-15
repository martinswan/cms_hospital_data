import requests

METASTORE_URL = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items"
THEME = "Hospitals"

resp = requests.get(METASTORE_URL, timeout=60)
resp.raise_for_status()
items = resp.json()
hospitals = [d for d in items if THEME in d.get("theme", [])]

print(hospitals)