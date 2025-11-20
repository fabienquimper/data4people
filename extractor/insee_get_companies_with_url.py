import time
from extract import postal_code as pc
from extract import insee_company as ic
from extract import scrapper as s
import polars as pl
import unicodedata
from ddgs import DDGS

# Pour utiliser: ./data# python -m extractor.insee_get_companies_with_url

# Configuration
CITY_LABEL = "Quimper"
LATITUDE = 47.996229
LONGITUDE = -4.102321
RADIUS_KM = 2
FILTRE_NAFS = ["56.10A", "56.10B", "56.30Z", "56.29A"]
nafs_s = "-".join(FILTRE_NAFS).replace(".", "-")
city_s = "".join(
        c for c in unicodedata.normalize("NFD", CITY_LABEL)
        if unicodedata.category(c) != "Mn"
).casefold()
EXPORT_FILE_NAME_CSV = f"insee_companies_urls__{city_s}__{nafs_s}.csv"

pl.Config.set_tbl_rows(150)   # Afficher toutes les lignes
pl.Config.set_tbl_cols(50)   # Afficher toutes les colonnes


print("##### VILLE: %s / LAT: %s / LONG: %s / RAYON KM: %s" % (CITY_LABEL, LATITUDE, LONGITUDE, RADIUS_KM))
print("##### Code NAF: %s" % " ".join(FILTRE_NAFS))
print("##### Chargement bases INSEE / OSM...")
post_code_obj = pc.PostalCode()
post_code_obj.set_radius_meters(RADIUS_KM * 1000)
post_code_obj.set_center(LATITUDE, LONGITUDE)

insee_res = post_code_obj.get_post_insee_codes_around()
print("##### Liste codes INSEE:")
print(insee_res)
insee_res_list = insee_res['#Code_commune_INSEE'].to_list()
# print(insee_res_list)

print("##### Chargement bases INSEE Entreprise...")
insee_companies = ic.InseeCompany()
companies = insee_companies.get_companies(insee_city_codes=insee_res_list, naf_codes=FILTRE_NAFS)
print(companies)

print("##### Scrapping d'URL d'entreprises...")
search_str_list = [[] for _ in range(5)]

rank = 1
for row in companies.iter_rows(named=True):
    name = row["enseigne1Etablissement"] or row["denominationUsuelleEtablissement"]
    search_str = (
        row["siret"] + " " +
        (name or "") + " " +
        row["codePostalEtablissement"] + " " +
        row["libelleVoieEtablissement"] + " " +
        row["libelleCommuneEtablissement"] + " " +
        row["activitePrincipaleEtablissement"]
    )
    raw_urls = []

    with DDGS() as ddg:
        try:
            results = ddg.text(search_str, max_results=5)
            for r in results:
                raw_urls.append(r.get("href", ""))
        except Exception as e:
            print(f"[WARN] Aucun résultat pour : {search_str} / {type(e)} / {e}")
            raw_urls = [""] * 5  # pour garder la structure propre

    # remplir les 5 colonnes correctement
    for i in range(5):
        search_str_list[i].append(raw_urls[i] if i < len(raw_urls) else "")

    print("Wait 3s ... (%s/%s)" % (rank, len(companies)))
    rank = rank + 1
    time.sleep(3)

# print(search_str_list)
companies_with_urls = companies
for i in range(5):
    companies_with_urls = companies_with_urls.with_columns(
        pl.Series(f"url_{i}", search_str_list[i])
    )

print("##### Companies with URLs:")
print(companies_with_urls)

print("##### Exportation vers CSV ... (./%s):" % EXPORT_FILE_NAME_CSV)
pl.from_dataframe(companies_with_urls).write_csv(EXPORT_FILE_NAME_CSV)
excel_file = EXPORT_FILE_NAME_CSV.replace(".csv", ".xlsx")
print("##### Exportation vers Excel ... (./%s):" % excel_file)
pl.from_dataframe(companies_with_urls).write_excel(excel_file)