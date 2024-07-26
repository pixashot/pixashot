import json
import os
from typing import Dict, Any

# Change the path to point to the root directory
TEMPLATES_FILE = os.path.join(os.path.dirname(__file__), '..', 'templates.json')


def load_templates() -> Dict[str, Dict[str, Any]]:
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, 'r') as f:
            return json.load(f)
    return {}


def get_template(name: str) -> Dict[str, Any]:
    templates = load_templates()
    return templates.get(name, {})


# Load templates once when the module is imported
TEMPLATES = load_templates()
