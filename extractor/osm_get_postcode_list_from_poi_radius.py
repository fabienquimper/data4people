from extract import postal_code as pc

# Musée Quimper
LATITUDE = 47.996229
LONGITUDE = -4.102321
RADIUS_KM = 7

post_code_obj = pc.PostalCode()
post_code_obj.set_radius_meters(RADIUS_KM * 1000)
post_code_obj.set_center(LATITUDE, LONGITUDE)

res = post_code_obj.get_post_insee_codes_around()

print(res)


print(res['#Code_commune_INSEE'].to_list())

# Pour lancer ce programme à la racine du projet: ./data# python -m extractor.osm_get_postcode_list_from_poi_radius

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