import requests
import pandas as pd
from geopy.distance import geodesic
from tqdm import tqdm
from datetime import datetime
from time import sleep
from pprint import pprint
import sys
from pathlib import Path
import polars as pl
import math

###############################################
# CONFIG
###############################################

# Import des configs
root = Path().resolve().parent  # remonte d'un niveau
# print(root)
sys.path.append(str(root))
from config import load_config
config = load_config()

###############################################
# PARAMÈTRES
###############################################
# Exemple : Mairie Quimper
LATITUDE = 47.996197
LONGITUDE = -4.102031
RAYON_KM = 0.3

# Codes NAF ciblés
NAF_CODES = ["56.10A", "56.10B", "56.30Z", "56.29A"]
API_KEY_INSEE = config['INSEE_API_KEY_INSEE']
# print("API_KEY_INSEE = ", API_KEY_INSEE)
url = "https://api.insee.fr/api-sirene/3.11/siret"

###############################################
# 1) Récupération Bars & Restaurants via OSM
###############################################
def get_osm_bars_restaurants(lat, lon, radius_km):
    url = "https://overpass-api.de/api/interpreter"

    # categorie = "bar|restaurant|cafe"
    categorie = "fast_food|restaurant|food_court"

    query = f"""
    [out:json];
    (
      node["amenity"~"{categorie}"](around:{radius_km*1000},{lat},{lon});
      way["amenity"~"{categorie}"](around:{radius_km*1000},{lat},{lon});
      relation["amenity"~"{categorie}"](around:{radius_km*1000},{lat},{lon});
    );
    out center;
    """

    response = requests.post(url, data={"data": query})
    data = response.json()

    rows = []
    for e in data["elements"]:
        name = e.get("tags", {}).get("name", "")
        amenity = e.get("tags", {}).get("amenity", "")
        lat = e.get("lat") or e.get("center", {}).get("lat")
        lon = e.get("lon") or e.get("center", {}).get("lon")
        addr = e.get("tags", {}).get("addr:full", "")
        street = e.get("tags", {}).get("addr:street", "")
        housenumber = e.get("tags", {}).get("addr:housenumber", "")
        city = e.get("tags", {}).get("addr:city", "")

        rows.append({
            "source": "OSM",
            "name": name,
            "category": amenity,
            "latitude": lat,
            "longitude": lon,
            "adresse": addr or f"{housenumber} {street} {city}".strip(),
        })

    return pd.DataFrame(rows)

###############################################
# 2) Récupération entreprises via SIRENE API
###############################################

file_code_postaux = "../data/raw/code_postaux_019HexaSmal_2025_11_22.csv"
postal_df = pl.read_csv(file_code_postaux,
                schema_overrides={
                    "#Code_commune_INSEE": pl.String,
                    "DEP": pl.String,
                    "REG": pl.String,
                    "COM_COMER": pl.String,  # si présent dans ce fichier
                }, separator=";"
                )

def get_insee_code_from_postal(postal_code, city_name):
    #print("Source: https://www.data.gouv.fr/datasets/base-officielle-des-codes-postaux/")
    return postal_df.filter(pl.col("Code_postal") == postal_code).filter(pl.col("Libell�_d_acheminement") == city_name)["#Code_commune_INSEE"][0]

def get_sirene_data(lat, lon, radius_km, naf_list, api_key):
    base_url = "https://api.insee.fr/api-sirene/3.11/siret"
    headers = {
        "X-INSEE-Api-Key-Integration": api_key
    }

    # Construire la query NAF
    naf_query = " OR ".join([f'activitePrincipaleUniteLegale:\'{naf}\'' for naf in naf_list])

    # Pagination
    rows = []
    page = 1
    size = 1000  # max 100 par page
    while True:
        # Quimper: 29232

        code_ville_insee = get_insee_code_from_postal(29000, "QUIMPER")

        params = {
            "q": f"({naf_query}) AND codeCommuneEtablissement:'{code_ville_insee}'",
            "page": page,
            "size": size
        }

        print("Param:")
        print(params)

        r = requests.get(base_url, headers=headers, params=params)
        if r.status_code != 200:
            print("Erreur SIRENE", r.status_code)
            print(r.text)
            break

        data = r.json()
        etablissements = data.get("etablissements", [])
        if not etablissements:
            break

        for e in etablissements:
            siret = e.get("siret")
            name = e["uniteLegale"].get("denominationUniteLegale", "")
            naf = e["uniteLegale"].get("activitePrincipaleUniteLegale", "")

            adr = e.get("adresseEtablissement", {})
            # address = f"{adr.get('numeroVoieEtablissement', '')} {adr.get('libelleVoieEtablissement', '')}, {adr.get('codePostalEtablissement', '')} {adr.get('libelleCommuneEtablissement', '')}".strip()
            # address = f"{adr.get('numeroVoieEtablissement', '')} {adr.get('libelleVoieEtablissement', '')}, {adr.get('codePostalEtablissement', '')} {adr.get('libelleCommuneEtablissement', '')}".strip()

            numero = adr.get("numeroVoieEtablissement") or ""
            voie = adr.get("libelleVoieEtablissement") or ""
            cp = adr.get("codePostalEtablissement") or ""
            commune = adr.get("libelleCommuneEtablissement") or ""
            address = f"{numero} {voie}, {cp} {commune}".strip().replace("  ", " ")

            lat_e = adr.get("latitudeEtablissement")
            lon_e = adr.get("longitudeEtablissement")

            # Si géolocalisation manquante, fallback sur Nominatim
            # if lat_e is None or lon_e is None:
            #     geo_url = "https://nominatim.openstreetmap.org/search"
            #     try:
            #         headers_geo = {"User-Agent": "MonScript/1.0 (Data4people)"}
            #         resp = requests.get(geo_url, headers=headers_geo,
            #                             params={"q": address, "format": "json", "limit": 1}, timeout=10)
            #         geo = resp.json() if resp.text else []
            #         print("For (%s %s)" % (lat_e, lon_e))
            #         print(geo)
            #     except Exception as e:
            #         print(f"Erreur géocodage Nominatim pour {address}: {e}")
            #         continue
            #
            #     if not geo:
            #         continue
            #     lat_e = float(geo[0]["lat"])
            #     lon_e = float(geo[0]["lon"])
            #
            # # dist = geodesic((lat, lon), (lat_e, lon_e)).km
            #
            # # Si coordonnées dispo, calculer distance
            # if lat_e is not None and lon_e is not None:
            #     dist = geodesic((lat, lon), (lat_e, lon_e)).km
            #     if dist > radius_km:
            #         continue
            #
            # # if dist > radius_km:
            # #     continue

            rows.append({
                "source": "SIRENE",
                "siret": siret,
                "name": name,
                "naf": naf,
                "adresse": address,
                "latitude": lat_e,
                "longitude": lon_e,
                # "distance_km": round(dist, 2)
                "brut": e
            })
            # time.sleep(1)

        if len(etablissements) < size:
            break
        page += 1

    return pd.DataFrame(rows)


# Get OSM from file
def osm_poi_restaurants_autour(df, lat0, lon0, rayon_m):
    R = 6371000.0

    lat0_rad = math.radians(lat0)
    lon0_rad = math.radians(lon0)

    # Réduit les données gérées
    lat_margin = 0.1   # ~ 11 km
    lat_margin = lat_margin * (rayon_m/1000) # (ex : pour 500m on prend une marge de 0.05 de lat soit 5.5km)
    lon_margin = 0.1   # ~ 7.5 km
    lon_margin = lon_margin * (rayon_m/1000) # (ex : pour 500m on prend une marge de 0.05 de lat soit 3.7km)

    return (
        df

        # Filtre latitude / longitude + type
        .filter(
                (pl.col("@lat").is_between(lat0 - lat_margin, lat0 + lat_margin)) &
                (pl.col("@lon").is_between(lon0 - lon_margin, lon0 + lon_margin)) &
                (pl.col("amenity").is_in(["restaurant", "fast_food", "food_court"]))
            )

        # radians
        .with_columns([
            pl.col("@lat").cast(pl.Float64).radians().alias("lat_rad"),
            pl.col("@lon").cast(pl.Float64).radians().alias("lon_rad"),
        ])

        # deltas
        .with_columns([
            (pl.col("lat_rad") - lat0_rad).alias("dlat"),
            (pl.col("lon_rad") - lon0_rad).alias("dlon"),
        ])

        # h = haversine
        .with_columns([
            (
                (pl.col("dlat") / 2).sin() ** 2
                + math.cos(lat0_rad)
                * pl.col("lat_rad").cos()
                * (pl.col("dlon") / 2).sin() ** 2
            ).alias("h")
        ])

        # Approximation arcsin(x)
        # arcsin(x) ≈ x * (1 + 0.5 * x^2) / sqrt(1 - x^2)
        .with_columns([
            pl.col("h").pow(0.5).alias("sqrt_h"),
            (1 - pl.col("h")).pow(0.5).alias("sqrt_1mh"),
        ])

        .with_columns([
            (
                2 * R *
                (
                    pl.col("sqrt_h") * (1 + 0.5 * pl.col("h"))
                    / pl.col("sqrt_1mh")
                )
            ).alias("distance_m")
        ])

        .filter(pl.col("distance_m") <= rayon_m)
        .sort("distance_m")

        .select([
            "@id", "@lat", "@lon", "name", "local_name",
            "amenity", "distance_m"
        ])
    )

####################################
# Extraction d'adresse à partir d'une geolocalisation
##################################

str_schema_full = {"id": pl.String, "numero_voix": pl.String, "voie": pl.String, "code_postal": pl.String, "ville": pl.String, "source": pl.String, "latitude": pl.Float32, "longitude": pl.Float32}

osm_df_full = pl.read_csv(
    "../data/raw/osm/full.csv/full.csv",
    infer_schema_length=0,
    try_parse_dates=False,
    schema_overrides=str_schema_full
)
# osm_df = osm_df.filter(pl.col("code_postal") == "29000")
# osm_df = osm_df.filter(pl.col("ville") == "Quimper")

# Get Street from latitude / longitude
def geoloc_match(df, lat_col, lon_col, lat0, lon0, tol_m=5):
    lat_tol = tol_m / 111320
    lon_tol = tol_m / (111320 * math.cos(math.radians(lat0)))

    return df.filter(
        (pl.col(lat_col).is_between(lat0 - lat_tol, lat0 + lat_tol)) &
        (pl.col(lon_col).is_between(lon0 - lon_tol, lon0 + lon_tol))
    )

def get_adresse_from_geoloc(osm_full, lat_col, lon_col):
    geo_data = geoloc_match(osm_full, "latitude", "longitude", lat_col, lon_col, tol_m=5)

    if len(geo_data) == 0:
        geo_data = geoloc_match(osm_full, "latitude", "longitude", lat_col, lon_col, tol_m=10)

    if len(geo_data) == 0:
        geo_data = geoloc_match(osm_full, "latitude", "longitude", lat_col, lon_col, tol_m=15)

    if len(geo_data) == 0:
        geo_data = geoloc_match(osm_full, "latitude", "longitude", lat_col, lon_col, tol_m=25)

    # print(geo_data)

    geo_adresse = geo_data['numero_voix'] + " " + geo_data['voie'] + " " + geo_data['code_postal'] + " " + geo_data['ville']
    return geo_adresse


def ajout_adresse(df_osm):
    addresses = []

    for r in df_osm.iter_rows(named=True):
        adr = get_adresse_from_geoloc(osm_df_full, r["@lat"], r["@lon"])
        adr_str = str(adr[0])  # si Series 1 valeur
        addresses.append(adr_str)

    df_osm = df_osm.with_columns(
        pl.Series("adresse", addresses)
    )
    return df_osm

def main():
    print("Récupération OSM par fichier …")
    df = pd.read_csv(
        "../data/raw/osm/poi.csv/poi.csv",
        sep="\t",
        engine="python",  # <--- ultra permissif
        on_bad_lines="skip"  # ou "warn"
    )
    oms_df = pl.from_pandas(df)
    print("Fichier chargé.")
    df = None
    df_osm = osm_poi_restaurants_autour(oms_df, LATITUDE, LONGITUDE, RAYON_KM * 1000)
    print(f"Nb restaurants: {len(df_osm)}")
    print("Sans adresse:")
    print(df_osm)
    print("Avec adresse:")
    df_osm = ajout_adresse(df_osm)
    print(df_osm)

    print("Récupération OSM par API …")
    df_osm_api = get_osm_bars_restaurants(LATITUDE, LONGITUDE, RAYON_KM)

    print(df_osm_api)

    dt_year = datetime.now().year
    dt_month = datetime.now().month
    dt_day = datetime.now().day
    dt_hour = datetime.now().hour
    dt_minute = datetime.now().minute
    file_name = f"bars_restaurants_mix_osm_sirene{dt_year}-{dt_month}-{dt_day}__{dt_hour}_{dt_minute}.csv"
    df_osm_api.to_csv("osm_api_" + file_name, sep=";", index=False)
    df_osm_pandas = df_osm.to_pandas()
    df_osm_pandas.to_csv("osm_from_file_" + file_name, sep=";", index=False)
    print(f"Fichier généré : 'osm_api_{file_name}'")
    print(f"Fichier généré : 'osm_from_file_{file_name}'")

    print("Récupération SIRENE …")
    df_sirene = get_sirene_data(
        LATITUDE,
        LONGITUDE,
        RAYON_KM,
        NAF_CODES,
        API_KEY_INSEE
    )
    print(df_sirene)
    df_sirene.to_csv("insee_" + file_name, sep=";", index=False)
    print(f"Fichier généré : 'insee_{file_name}'")

    print("Type …")
    print("type(df_osm_api) = ", type(df_osm_api))
    print("type(df_osm_pandas) = ", type(df_osm_pandas))
    print("type(df_sirene) = ", type(df_sirene))

    print("Fusion …")
    df_fusion = pd.concat([df_osm_api, df_sirene, df_osm_pandas], ignore_index=True)
    df_fusion.to_csv("fusion_" + file_name, sep=";", index=False)
    print(f"Fichier généré : 'fusion_{file_name}'")
    print("Type …")
    print("type(df_fusion) = ", type(df_fusion))

if __name__ == "__main__":
    main()