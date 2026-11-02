# backend/

API FastAPI + motores científicos do Alloy Virtual Lab (Python >= 3.11).
Base: CrystaLab v1.1.0 (_origem/B). Arquitetura em docs/ARQUITETURA_FINAL.md.

Regra de dependência (verificada por teste em backend/tests/unit/test_arquitetura.py, Fase 3):
api -> services -> (engines | repositories) -> models ; engines não importam api, services, repositories nem models.
