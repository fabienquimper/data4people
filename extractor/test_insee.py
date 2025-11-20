import requests
from pprint import pprint
import sys
from pathlib import Path

# Import des configs
root = Path(__file__).resolve().parents[1]  # remonte 1 niveau
sys.path.append(str(root))
from config import load_config
config = load_config()

api_key = config['INSEE_API_KEY_INSEE']
url = "https://api.insee.fr/api-sirene/3.11/siret"
headers = {"X-INSEE-Api-Key-Integration": api_key}

# naf_codes = ["56.21Z"] # traiteur
# naf_codes = ["56.21Z", "56.10C"] # traiteur
naf_codes = ["56.10C"] # traiteur , restauration rapide
# naf_codes = ["56.10A","56.10B","56.30Z"]
naf_query = " OR ".join([f"activitePrincipaleUniteLegale:{naf}" for naf in naf_codes])

params = {"q": f"{naf_query} AND codeCommuneEtablissement:29232", "page":1, "size":5}

r = requests.get(url, headers=headers, params=params)

print(r.status_code)
print(r.json())
print(r.json().keys())

import json

print(json.dumps(r.json(), indent=4, ensure_ascii=False))