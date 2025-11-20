from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import requests
import json
import re

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"   # ou "mistral", "qwen2", etc.

# -------------------------------------------------------
# FastAPI App
# -------------------------------------------------------

app = FastAPI(title="Local LLM API",
              description="LLM Local via Ollama + API de mapping de catégories")

# ---------------------
# Input schemas
# ---------------------

class AskRequest(BaseModel):
    prompt: str

class GenerateNeutralCategoriesRequest(BaseModel):
    list_a: list
    list_b: list

class AssignNeutralCategoryRequest(BaseModel):
    category: str
    neutral_categories: list

# -------------------------------------------------------
# Ollama Integration
# -------------------------------------------------------

def ask_ollama(prompt: str) -> str:
    """Envoie un prompt au modèle local via Ollama"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()

def extract_json(text: str):
    """Essaie d’extraire un JSON depuis une réponse LLM"""
    match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None

# -------------------------------------------------------
# API Endpoints
# -------------------------------------------------------

@app.post("/generate_neutral_categories")
def generate_neutral_categories(req: GenerateNeutralCategoriesRequest):
    """
    Génère un ensemble de catégories neutres à partir de deux listes.
    """
    prompt = f"""
Tu es un expert en harmonisation de catégories.
On te donne deux listes de catégories provenant de datasets différents.

Liste A :
{json.dumps(req.list_a, indent=2)}

Liste B :
{json.dumps(req.list_b, indent=2)}

Ta mission :
- Propose un ensemble de catégories neutres (max 20) pour regrouper ces catégories.
- Fournis un alias simple pour chaque catégorie.
- Réponds uniquement en JSON valide :
[
  {{"name": "Nom catégorie neutre", "alias": "alias_simple"}},
  ...
]
"""
    answer = ask_ollama(prompt)

    try:
        data = json.loads(answer)
    except json.JSONDecodeError:
        data = extract_json(answer)

    if not data:
        return {"error": "Impossible d'extraire les catégories neutres depuis la réponse LLM",
                "raw_response": answer}

    return data

@app.post("/assign_neutral_category")
def assign_neutral_category(req: AssignNeutralCategoryRequest):
    """
    Pour 1 catégorie du dataset, trouve la meilleure catégorie neutre.
    """
    prompt = f"""
On te donne une catégorie provenant d'un dataset :
"{req.category}"

Et la liste des catégories neutres :
{json.dumps(req.neutral_categories, indent=2)}

Ta mission :
- Retourne la catégorie neutre la plus adaptée à cette catégorie.
- Ne réponds **que** par un JSON valide :
{{
    "neutral_category": "nom de la catégorie neutre",
    "alias": "alias de la catégorie neutre",
    "explanation": "courte explication"
}}
"""
    answer = ask_ollama(prompt)

    try:
        data = json.loads(answer)
    except json.JSONDecodeError:
        data = extract_json(answer)

    if not data:
        return {"error": "Impossible d’extraire la catégorie neutre depuis la réponse LLM",
                "raw_response": answer}

    return data

@app.post("/ask")
def ask(req: AskRequest):
    """Demande libre au LLM"""
    answer = ask_ollama(req.prompt)
    return {"response": answer}


# -------------------------------------------------------
# Run Server
# -------------------------------------------------------

if __name__ == "__main__":
    print("🚀 Serveur LLM local démarré : http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
