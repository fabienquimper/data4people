import requests

try:
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3", "prompt": "Quelle la capitale de la France ?", "stream": False},
    )
    print("Réponse du modèle :\n", r.json()["response"])

except Exception as e:
    print("❌ Erreur : Ollama ne semble pas démarré.")
    print("Démarre-le avec : sudo systemctl start ollama")
    print(e)
