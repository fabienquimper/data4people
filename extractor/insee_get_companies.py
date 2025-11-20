from extract import postal_code as pc
from extract import insee_company as ic
import polars as pl

# Musée Quimper
CITY_LABEL = "Quimper"
LATITUDE = 47.996229
LONGITUDE = -4.102321
RADIUS_KM = 1
FILTRE_NAFS = ["56.10A", "56.10B", "56.30Z", "56.29A"]

pl.Config.set_tbl_rows(150)   # Afficher toutes les lignes
pl.Config.set_tbl_cols(50)   # Afficher toutes les colonnes

print("##### VILLE / LAT / LONG / RAYON KM:", (CITY_LABEL, LATITUDE, LONGITUDE, RADIUS_KM))
print("##### Code NAF:", FILTRE_NAFS)
print("##### Chargement bases INSEE / OSM...")
post_code_obj = pc.PostalCode()
post_code_obj.set_radius_meters(RADIUS_KM * 1000)
post_code_obj.set_center(LATITUDE, LONGITUDE)

insee_res = post_code_obj.get_post_insee_codes_around()
print("##### Liste codes INSEE:")
print(insee_res)
insee_res_list = insee_res['#Code_commune_INSEE'].to_list()
print(insee_res_list)

print("##### Chargement bases INSEE Entreprise...")

insee_companies = ic.InseeCompany()
companies = insee_companies.get_companies(insee_city_codes=insee_res_list, naf_codes=FILTRE_NAFS)

print(companies)

# Pour lancer ce programme à la racine du projet: ./data# python -m extractor.insee_get_companies

'''
OUTPUT

shape: (28, 5)
┌─────────────┬─────────────────────┬──────────────────────┬──────────────────────┬─────────┐
│ code_postal ┆ #Code_commune_INSEE ┆ Nom_de_la_commune    ┆ ville                ┆ Ligne_5 │
│ ---         ┆ ---                 ┆ ---                  ┆ ---                  ┆ ---     │
│ str         ┆ str                 ┆ str                  ┆ str                  ┆ str     │
╞═════════════╪═════════════════════╪══════════════════════╪══════════════════════╪═════════╡
│ 29700       ┆ 29170               ┆ PLOMELIN             ┆ PLOMELIN             ┆ null    │
│ 29700       ┆ 29216               ┆ PLUGUFFAN            ┆ PLUGUFFAN            ┆ null    │
│ 29510       ┆ 29020               ┆ BRIEC                ┆ BRIEC                ┆ null    │
│ 29510       ┆ 29048               ┆ EDERN                ┆ EDERN                ┆ null    │
│ 29510       ┆ 29106               ┆ LANDREVARZEC         ┆ LANDREVARZEC         ┆ null    │
│ …           ┆ …                   ┆ …                    ┆ …                    ┆ …       │
│ 29710       ┆ 29159               ┆ PEUMERIT             ┆ PEUMERIT             ┆ null    │
│ 29710       ┆ 29167               ┆ PLOGASTEL ST GERMAIN ┆ PLOGASTEL ST GERMAIN ┆ null    │
│ 29710       ┆ 29173               ┆ PLONEIS              ┆ PLONEIS              ┆ null    │
│ 29710       ┆ 29215               ┆ PLOZEVET             ┆ PLOZEVET             ┆ null    │
│ 29710       ┆ 29225               ┆ POULDREUZIC          ┆ POULDREUZIC          ┆ null    │
└─────────────┴─────────────────────┴──────────────────────┴──────────────────────┴─────────┘
'''