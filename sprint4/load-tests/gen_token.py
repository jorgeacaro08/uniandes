"""Genera tokens JWT HS256 para las pruebas locales/JMeter (modo AUTH_PROVIDER=local).

Uso:
  python gen_token.py                       -> token valido para NIT900000000
  python gen_token.py NIT900000001          -> token para otra empresa
  python gen_token.py NIT900000000 admin    -> token con rol admin (acceso global)
El secreto debe coincidir con AUTH_SECRET de ms-reportes (por defecto 'dev-secret').
"""
import os
import sys
import time

import jwt


def make_token(empresa, roles=None, secret=None, exp_min=120):
    secret = secret or os.getenv("AUTH_SECRET", "dev-secret")
    now = int(time.time())
    payload = {
        "sub": "jmeter-user",
        "empresa": empresa,
        "roles": roles or ["finanzas"],
        "iat": now,
        "exp": now + exp_min * 60,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


if __name__ == "__main__":
    empresa = sys.argv[1] if len(sys.argv) > 1 else "NIT900000000"
    roles = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    print(make_token(empresa, roles))
