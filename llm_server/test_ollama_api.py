import requests
import json

BASE_URL = "http://localhost:8000"

def pretty_print(title, response):
    print("\n" + "="*80)
    print(title)
    print("="*80)
    try:
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception:
        print("Erreur de parsing JSON :", response.text)


# 1️⃣ Tester l’endpoint /ask
payload_ask = {
    "prompt": "Explique moi ce qu’est un dataset open data"
}

response_ask = requests.post(f"{BASE_URL}/ask", json=payload_ask)
pretty_print("Réponse /ask", response_ask)


# 2️⃣ Test correspondance entre deux jeux de catégories
payload_match = {
    "list_a": ["Brocante", "Marché", "Conférence"],
    "list_b": ["Vide-greniers", "Marchés alimentaires", "Conférences-débats", "Animations diverses"]
}

response_match = requests.post(f"{BASE_URL}/match_categories", json=payload_match)
pretty_print("Réponse /match_categories", response_match)


# 3️⃣ Test mapping d’une seule catégorie
payload_map = {
    "category": "Conférence",
    "list_b": ["Vide-greniers", "Marché alimentaire", "Conférences-débats"]
}

response_map = requests.post(f"{BASE_URL}/map_category", json=payload_map)
pretty_print("Réponse /map_category", response_map)
