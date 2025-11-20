from extract import postal_code as pc

post_code_obj = pc.PostalCode()
res = post_code_obj.get_insee_code_from_postal("29000")

print(res)
print(res)

'''
OUTPUT

(.venv) root@MSI:/mnt/c/git/data# python -m extractor.osm_get_insee_code
shape: (1, 5)
┌─────────────────────┬───────────────────┬─────────────┬────────────────────────┬─────────┐
│ #Code_commune_INSEE ┆ Nom_de_la_commune ┆ Code_postal ┆ Libell�_d_acheminement ┆ Ligne_5 │
│ ---                 ┆ ---               ┆ ---         ┆ ---                    ┆ ---     │
│ str                 ┆ str               ┆ i64         ┆ str                    ┆ str     │
╞═════════════════════╪═══════════════════╪═════════════╪════════════════════════╪═════════╡
│ 29232               ┆ QUIMPER           ┆ 29000       ┆ QUIMPER                ┆ null    │
└─────────────────────┴───────────────────┴─────────────┴────────────────────────┴─────────┘
(.venv) root@MSI:/mnt/c/git/ai/exercices/data#
'''