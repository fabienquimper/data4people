import polars as pl
import math
import pandas as pd
from numpy.matlib import empty
import typing

class InseeCompany:
    def __init__(self):
        pass

    def get_companies(self, insee_city_codes: list, naf_codes: list) -> list:
        a = pl.scan_parquet("data/raw/insee/StockEtablissement_utf8.parquet")

        # Lecture "lazy" du Parquet (ne charge rien en mémoire)
        lazy_df = pl.scan_parquet("data/raw/insee/StockEtablissement_utf8.parquet")

        # On filtre directement sur la colonne codeCommuneEtablissement
        filtered_df = (
            lazy_df
            .filter(pl.col("codeCommuneEtablissement").is_in(insee_city_codes))
            .filter(pl.col("activitePrincipaleEtablissement").is_in(naf_codes))
            .filter(pl.col("caractereEmployeurEtablissement") == "N")
            .filter(pl.col("etatAdministratifEtablissement") == "A")
            .select([
                "siren",
                "siret",
                "codePostalEtablissement",
                "activitePrincipaleEtablissement",
                "enseigne1Etablissement",
                "denominationUsuelleEtablissement",
                "codeCommuneEtablissement",
                # "numeroVoieEtablissement",
                # "typeVoieEtablissement",
                "libelleVoieEtablissement",
                # "codePostalEtablissement",
                "libelleCommuneEtablissement",
                # "coordonneeLambertAbscisseEtablissement",
                # "coordonneeLambertOrdonneeEtablissement"
            ])
            .collect()  # ici on charge uniquement les lignes filtrées
        )

        # filtered_df.write_csv("insee_44.csv")

        # No: codeCommuneEtablissement, codePostalEtablissement

        return filtered_df


'''

['siren',
 'nic',
 'siret',
 'statutDiffusionEtablissement',
 'dateCreationEtablissement',
 'trancheEffectifsEtablissement',
 'anneeEffectifsEtablissement',
 'activitePrincipaleRegistreMetiersEtablissement',
 'dateDernierTraitementEtablissement',
 'etablissementSiege',
 'nombrePeriodesEtablissement',
 'complementAdresseEtablissement',
 'numeroVoieEtablissement',
 'indiceRepetitionEtablissement',
 'dernierNumeroVoieEtablissement',
 'indiceRepetitionDernierNumeroVoieEtablissement',
 'typeVoieEtablissement',
 'libelleVoieEtablissement',
 'codePostalEtablissement',
 'libelleCommuneEtablissement',
 'libelleCommuneEtrangerEtablissement',
 'distributionSpecialeEtablissement',
 'codeCommuneEtablissement',
 'codeCedexEtablissement',
 'libelleCedexEtablissement',
 'codePaysEtrangerEtablissement',
 'libellePaysEtrangerEtablissement',
 'identifiantAdresseEtablissement',
 'coordonneeLambertAbscisseEtablissement',
 'coordonneeLambertOrdonneeEtablissement',
 'complementAdresse2Etablissement',
 'numeroVoie2Etablissement',
 'indiceRepetition2Etablissement',
 'typeVoie2Etablissement',
 'libelleVoie2Etablissement',
 'codePostal2Etablissement',
 'libelleCommune2Etablissement',
 'libelleCommuneEtranger2Etablissement',
 'distributionSpeciale2Etablissement',
 'codeCommune2Etablissement',
 'codeCedex2Etablissement',
 'libelleCedex2Etablissement',
 'codePaysEtranger2Etablissement',
 'libellePaysEtranger2Etablissement',
 'dateDebut',
 'etatAdministratifEtablissement',
 'enseigne1Etablissement',
 'enseigne2Etablissement',
 'enseigne3Etablissement',
 'denominationUsuelleEtablissement',
 'activitePrincipaleEtablissement',
 'nomenclatureActivitePrincipaleEtablissement',

'''