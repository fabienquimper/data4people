import requests
import csv
import time
from geopy.distance import geodesic
import sys
from pathlib import Path

# Import des configs
root = Path().resolve().parent  # remonte d'un niveau
# print(root)
sys.path.append(str(root))
from config import load_config
config = load_config()

API_KEY = config["GMAPS_API_KEY_INSEE"]

# ----------------------------------------------------------
# 1) Fonction pour obtenir les coordonnées d'une ville
# ----------------------------------------------------------
def geocode_city(city_name):
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": city_name, "key": API_KEY}

    res = requests.get(url, params=params).json()
    if res["status"] != "OK":
        raise Exception("Ville introuvable")

    location = res["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]

# ----------------------------------------------------------
# 2) Recherche d'établissements par secteur & rayon
# ----------------------------------------------------------
def search_places(lat, lng, radius, keywords, type = "establishment"):
    places = []
    next_page_token = None

    while True:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": type,
            "keyword": " ".join(keywords),
            "key": API_KEY
        }

        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(2)

        response = requests.get(url, params=params).json()

        if "results" in response:
            places.extend(response["results"])

        next_page_token = response.get("next_page_token")
        if not next_page_token:
            break

    return places

# ----------------------------------------------------------
# 3) Récupérer les détails supplémentaires des entreprises
# ----------------------------------------------------------
def get_place_details(place_id):
    url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,website,formatted_phone_number,"
                  "types,business_status,editorial_summary,geometry",
        "key": API_KEY
    }
    res = requests.get(url, params=params).json()
    return res.get("result", {})

# ----------------------------------------------------------
# 4) Export CSV
# ----------------------------------------------------------
def export_to_csv(data, filename="entreprises.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"CSV exporté : {filename}")

from staticmap import StaticMap, CircleMarker
from PIL import Image

def export_map_as_png(final_data, output_png="carte.png"):
    if not final_data:
        raise ValueError("final_data est vide")

    # Taille de la carte
    m = StaticMap(800, 600)

    # Ajout des points
    for item in final_data:
        marker = CircleMarker((item["lng"], item["lat"]), 'red', 12)
        m.add_marker(marker)

    # Rendu en image
    image = m.render()
    image.save(output_png)

    print("Image générée :", output_png)
    return output_png

import folium

def afficher_carte(final_data):
    if not final_data:
        raise ValueError("final_data est vide !")

    # Centrage sur le premier point
    center_lat = final_data[0]["lat"]
    center_lng = final_data[0]["lng"]

    # Création de la carte
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13)

    # Ajout des marqueurs
    for item in final_data:
        popup_txt = (
            f"<b>{item['nom']}</b><br>"
            f"{item['adresse']}<br>"
            f"Distance : {item['distance']:.2f} km<br>"
        )

        folium.Marker(
            [item["lat"], item["lng"]],
            popup=popup_txt
        ).add_to(m)

    # Save map
    m.save("map.html")
    export_map_as_png(final_data, "map.png")
    return m

# ----------------------------------------------------------
# 5) Programme principal
# ----------------------------------------------------------
def main():
    ville = "Quimper"
    rayon = 4000  # 4km
    secteurs = ["restaurant", "bar", "cafe"]

    lat, lng = geocode_city(ville)

    print(f"Recherche autour de {ville} ({lat},{lng})...")

    results = search_places(lat, lng, rayon, secteurs, "point_of_interest")

    final_data = []
    for r in results:
        details = get_place_details(r["place_id"])
        print(details)
        lat_e = float(details.get("geometry", {}).get("location", {}).get("lat"))
        lon_e = float(details.get("geometry", {}).get("location", {}).get("lng"))

        dist = geodesic((lat, lng), (lat_e, lon_e)).km

        final_data.append({
            "nom": details.get("name"),
            "adresse": details.get("formatted_address"),
            "telephone": details.get("formatted_phone_number"),
            "site_web": details.get("website"),
            "secteurs": ", ".join(details.get("types", [])),
            "description": details.get("editorial_summary", {}).get("overview", ""),
            "lat": lat_e,
            "lng": lon_e,
            "distance": dist
        })
    final_data.sort(key=lambda x: x["distance"])

    afficher_carte(final_data)

if __name__ == "__main__":
    main()
