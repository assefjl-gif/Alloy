"""Gera docs/openapi.json a partir da aplicação (fonte dos tipos TypeScript na Fase 5, ADR-007).

Uso (na raiz): .venv/Scripts/python scripts/exportar_openapi.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

esquema = create_app(Settings(_env_file=None, env="dev"), motor_banco=None).openapi()
destino = RAIZ / "docs" / "openapi.json"
destino.write_text(json.dumps(esquema, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"{len(esquema['paths'])} rotas, {len(esquema['components']['schemas'])} schemas → {destino.relative_to(RAIZ)}")
