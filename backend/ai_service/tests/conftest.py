import sys
from pathlib import Path

# Ensure backend/ai_service is on sys.path so tests can import `utils` as a top-level package
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
