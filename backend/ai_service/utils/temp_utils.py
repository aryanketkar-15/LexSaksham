from pathlib import Path
import json

T_PATH = Path(__file__).resolve().parents[1] / "models" / "temperature.json"

def load_temperature(default=1.0):
    try:
        if T_PATH.exists():
            with open(T_PATH, "r") as f:
                return float(json.load(f).get("temperature", default))
    except Exception:
        pass
    return default
