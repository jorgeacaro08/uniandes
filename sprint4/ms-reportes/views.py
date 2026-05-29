from fastapi import APIRouter, Request, HTTPException

import auth
from db import get_collection

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/reportes")
def get_reporte(empresa: str, periodo: str, request: Request):
    """Sirve el reporte consolidado precalculado (lectura de 1 documento).

    Flujo: autenticar -> autorizar por empresa -> leer documento indexado.
    """
    try:
        claims = auth.authenticate(request.headers.get("authorization"))
        auth.authorize_empresa(claims, empresa)
    except auth.AuthError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail)

    coll = get_collection()
    doc = coll.find_one({"empresa": empresa, "periodo": periodo}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="reporte no encontrado")
    return doc
