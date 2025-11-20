import polars as pl
import math

class PostalCode:
    def load_osm_full(self):
        str_schema = {"id": pl.String, "numero_voix": pl.String, "voie": pl.String, "code_postal": pl.String,
                      "ville": pl.String, "source": pl.String, "latitude": pl.Float32, "longitude": pl.Float32}

        self.osm_df = pl.read_csv(
            # "../data/raw/osm/full.csv/full.csv",
            "data/raw/osm/full.csv/full.csv",
            infer_schema_length=0,
            try_parse_dates=False,
            schema_overrides=str_schema
        )

    def load_post_codes(self):
        file_code_postaux = "data/raw/code_postaux_019HexaSmal_2025_11_22.csv"
        self.postal_df = pl.read_csv(file_code_postaux,
                                schema_overrides={
                                    "#Code_commune_INSEE": pl.String,
                                    "DEP": pl.String,
                                    "REG": pl.String,
                                    "COM_COMER": pl.String,  # si présent dans ce fichier
                                }, separator=";"
                                )

    def __init__(self):
        self.postal_df = None
        self.osm_df = None
        self.radius_meters = None
        self.lng = None
        self.lat = None
        self.load_osm_full()
        self.load_post_codes()

    def set_center(self, lat, lng):
        self.lat = lat
        self.lng = lng

    def set_radius_meters(self, radius):
        self.radius_meters = radius

    def osm_around_post_code_autour(self):
        rayon_m = self.radius_meters
        lat0 = self.lat
        lon0 = self.lng

        # make sure to have enough addresses
        if rayon_m <= 500:
            rayon_m = 500

        # Rayon de la terre
        R = 6371000.0

        lat0_rad = math.radians(lat0)
        lon0_rad = math.radians(lon0)

        # Réduit les données gérées
        lat_margin = 0.1  # ~ 11 km
        lat_margin = lat_margin * (rayon_m / 1000)  # (ex : pour 500m on prend une marge de 0.05 de lat soit 5.5km)
        lon_margin = 0.1  # ~ 7.5 km
        lon_margin = lon_margin * (rayon_m / 1000)  # (ex : pour 500m on prend une marge de 0.05 de lat soit 3.7km)

        places = (
            self.osm_df

            # Filtre latitude / longitude + type
            .filter(
                (pl.col("latitude").is_between(lat0 - lat_margin, lat0 + lat_margin)) &
                (pl.col("longitude").is_between(lon0 - lon_margin, lon0 + lon_margin))
            )
            # radians
            .with_columns([
                pl.col("latitude").cast(pl.Float64).radians().alias("lat_rad"),
                pl.col("longitude").cast(pl.Float64).radians().alias("lon_rad"),
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
        )

        # print(places)

        return ( places.filter(pl.col("distance_m") <= rayon_m)
                .sort("distance_m")
                .select("code_postal")
                # .select("code_postal", "ville")
                .unique()
            )

    # def get_insee_code_from_postal(self, postal_code, city_name):
    def get_insee_code_from_postal(self, postal_code):
        # print("Source: https://www.data.gouv.fr/datasets/base-officielle-des-codes-postaux/")
        return self.postal_df.filter(pl.col("Code_postal") == int(postal_code))
        # return postal_df.filter(pl.col("Code_postal") == int(postal_code)).filter(pl.col("Libell�_d_acheminement") == city_name.upper())

    def get_post_insee_codes_around(self):
        postal_ref = self.postal_df.rename({
            "Code_postal": "code_postal",
            "Libell�_d_acheminement": "ville"
        }).with_columns(
            pl.col("code_postal").cast(pl.String)
        )

        osm_df2 = self.osm_around_post_code_autour()

        # print("COUNT osm_df2 = ", len(osm_df2))
        # print(osm_df2)

        merged = osm_df2.join(postal_ref, on=["code_postal"], how="left")
        # merged = osm_df2.join(postal_ref, on=["code_postal", "ville"], how="left")

        # print(merged)

        merged2 = merged.with_columns(
            pl.col("code_postal").cast(pl.String)
        ).filter(pl.col("#Code_commune_INSEE").is_not_null())

        # print(merged2)
        return merged2