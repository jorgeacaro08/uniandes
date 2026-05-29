"""Manejador de autenticacion y autorizacion (tactica de seguridad).

Encapsula al proveedor de identidad detras de una sola interfaz: cambiar de
proveedor (Auth0 -> Keycloak, etc.) solo requiere tocar este modulo => sustenta
el ASR de mantenibilidad (1 componente, defer binding por configuracion).

Variables de entorno:
  AUTH_ENABLED   true|false  -> activa/desactiva la seguridad (prueba de trade-off)
  AUTH_PROVIDER  local|auth0 -> selecciona el proveedor (punto unico de cambio)
  AUTH_SECRET                -> secreto HS256 para el modo local/pruebas
  AUTH0_DOMAIN, AUTH0_AUDIENCE -> validacion RS256 contra Auth0 (produccion)
"""
import os


class AuthError(Exception):
    def __init__(self, status, detail):
        self.status = status
        self.detail = detail
        super().__init__(detail)


def _enabled():
    return os.getenv("AUTH_ENABLED", "true").lower() == "true"


def verify_token(token):
    """Valida la firma/claims del token segun el proveedor configurado."""
    import jwt

    provider = os.getenv("AUTH_PROVIDER", "local")
    if provider == "auth0":
        domain = os.getenv("AUTH0_DOMAIN")
        audience = os.getenv("AUTH0_AUDIENCE")
        jwks_client = jwt.PyJWKClient(f"https://{domain}/.well-known/jwks.json")
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=f"https://{domain}/",
        )
    # Modo local/pruebas: HS256 con secreto compartido (reproducible en JMeter).
    secret = os.getenv("AUTH_SECRET", "dev-secret")
    return jwt.decode(token, secret, algorithms=["HS256"])


def authenticate(authorization_header):
    """Autentica al actor. Devuelve los claims o lanza AuthError (401)."""
    if not _enabled():
        # Seguridad desactivada: ruta usada solo para la prueba de trade-off.
        return {"sub": "anon", "empresa": "*", "roles": ["finanzas-global"]}
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise AuthError(401, "token ausente")
    token = authorization_header.split(" ", 1)[1]
    try:
        return verify_token(token)
    except Exception as exc:  # firma invalida, expirado, etc.
        raise AuthError(401, f"token invalido: {exc}")


def authorize_empresa(claims, empresa):
    """Autoriza por alcance: el actor solo puede leer reportes de SU empresa."""
    if not _enabled():
        return
    roles = claims.get("roles") or claims.get("permissions") or []
    if "admin" in roles or "finanzas-global" in roles:
        return
    claim_empresa = claims.get("empresa") or claims.get("https://bite.co/empresa")
    if claim_empresa != empresa:
        raise AuthError(403, "no autorizado para los reportes de esta empresa")
