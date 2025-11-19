from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
STEP_DIR = BACKEND_DIR.parent
REPO_ROOT = STEP_DIR.parent

for env_file in [BACKEND_DIR / ".env", STEP_DIR / ".env", REPO_ROOT / ".env"]:
    if env_file.exists():
        for raw in env_file.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import ingest_articles, ARTICLES_DIR, VSTORE_DIR

if __name__ == "__main__":
    ingest_articles(ARTICLES_DIR, VSTORE_DIR)
    print(f"vectorstore saved to {VSTORE_DIR}")
