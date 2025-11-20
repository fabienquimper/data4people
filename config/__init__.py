import os
import yaml

def load_config():
    env = os.getenv("ENV", "dev")  # dev par défaut
    path = f"{os.path.dirname(__file__)}/{env}.yaml"

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
