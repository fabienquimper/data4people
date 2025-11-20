import polars as pl
import pandas as pd
import unicodedata
import re
import requests
import json

# -------------------------------------------------------------------
# 🔧 Fichiers source
# -------------------------------------------------------------------
DATASET_1_PATH = "../data/raw/234400034_070-002_offre-touristique-fetes_et_manifestations-rpdl@paysdelaloire.csv"
DATASET_2_PATH = "../data/raw/bretagne-fetes-et-manifestations.csv"

DATASET_1_NAME = "paysdelaloire.csv"
DATASET_2_NAME = "bretagne-fetes-et-manifestations.csv"

# -------------------------------------------------------------------
# 🔧 Colonnes contenant les catégories
# -------------------------------------------------------------------
COL_CAT_PDL = "Catégorie de la fête ou manifestation"
COL_CAT_BZH = "DetailIDENTFMATYPE"

# -------------------------------------------------------------------
# 🛠️ Fonction pour produire un alias simple
# -------------------------------------------------------------------
def normalize_alias(text):
    if text is None or str(text).strip() == "":
        return ""
    text = str(text).lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")

# -------------------------------------------------------------------
# 📥 Chargement des datasets
# -------------------------------------------------------------------
df_pdl = pl.read_csv(DATASET_1_PATH, separator=";", infer_schema_length=50000)
df_bzh = pl.read_csv(DATASET_2_PATH, separator=";", infer_schema_length=50000)

cats_pdl = [c for c in df_pdl.select(pl.col(COL_CAT_PDL)).unique().to_series().to_list() if c not in [None, ""]]
cats_bzh = [c for c in df_bzh.select(pl.col(COL_CAT_BZH)).unique().to_series().to_list() if c not in [None, ""]]

print(f"🔹 Catégories PDL ({len(cats_pdl)}) : {cats_pdl}")
print(f"🔹 Catégories BZH ({len(cats_bzh)}) : {cats_bzh}")

BASE_URL = "http://localhost:8000"

# -------------------------------------------------------------------
# 🔗 Appel API pour générer les catégories neutres
# -------------------------------------------------------------------
def generate_neutral_categories(list_a, list_b):
    payload = {"list_a": list_a, "list_b": list_b}
    response = requests.post(f"{BASE_URL}/generate_neutral_categories", json=payload)
    data = response.json()
    return data  # liste de {"name": ..., "alias": ...}

neutral_categories = generate_neutral_categories(cats_pdl, cats_bzh)
print(f"⚡ Catégories neutres générées ({len(neutral_categories)}): {neutral_categories}")

# -------------------------------------------------------------------
# 🔗 Fonction pour assigner catégorie neutre
# -------------------------------------------------------------------
def assign_neutral_category(category):
    payload = {"category": category, "neutral_categories": neutral_categories}
    response = requests.post(f"{BASE_URL}/assign_neutral_category", json=payload)
    data = response.json()
    return data  # {"neutral_category": ..., "alias": ..., "explanation": ...}

# -------------------------------------------------------------------
# 📘 Construction du CSV final
# -------------------------------------------------------------------
rows = []

for c in cats_pdl:
    ncat = assign_neutral_category(c)
    rows.append([
        DATASET_1_NAME,
        c,
        ncat.get("neutral_category", ""),
        ncat.get("alias", "")
    ])

for c in cats_bzh:
    ncat = assign_neutral_category(c)
    rows.append([
        DATASET_2_NAME,
        c,
        ncat.get("neutral_category", ""),
        ncat.get("alias", "")
    ])

# -------------------------------------------------------------------
# 💾 Export CSV
# -------------------------------------------------------------------
output_path = "table_correspondance_categories.csv"
# df_out = pd.DataFrame(rows, columns=["NOMDUDATASET", "CATEGORIE_DU_DATASET", "CATEGORIE_GENERE", "ALIAS_GENERE"])
df_out = pd.DataFrame(rows, columns=["dataset", "categorie_dataset", "categorie_neutre", "alias"])
df_out.to_csv(output_path, sep=";", index=False, encoding="utf-8")

print(f"✔ CSV généré : {output_path}")
