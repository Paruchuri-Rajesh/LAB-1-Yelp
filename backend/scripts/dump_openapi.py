"""Small helper to dump the FastAPI OpenAPI spec to a file.
Run from the repository root (or backend) with the active virtualenv.
"""
import json
import os

# ensure backend is importable when running from repo root
import sys
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from app.main import create_app

app = create_app()
openapi = app.openapi()

out_path = os.path.join(os.getcwd(), "backend", "openapi.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(openapi, f, indent=2, ensure_ascii=False)

print(f"Wrote OpenAPI JSON to {out_path}")
