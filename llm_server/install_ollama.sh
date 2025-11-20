#!/bin/bash

echo "🔵 Installation d’Ollama…"

# Téléchargement et installation
curl -fsSL https://ollama.com/install.sh | sh

echo "✔ Ollama installé."

echo "🔵 Démarrage du service Ollama…"
sudo systemctl start ollama

echo "✔ Service démarré."

echo "🔵 Téléchargement du modèle LLaMA 3 (8B par défaut)…"
ollama pull llama3

echo "✔ Modèle téléchargé !"

echo "💡 Test rapide :"
echo "  ollama run llama3 \"Bonjour !\""
