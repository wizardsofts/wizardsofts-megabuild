"""
JWT Validation for Keycloak-issued tokens

SECURITY: All backend endpoints must validate JWT tokens from auth.guardianinvestmentbd.com
Uses python-jose 3.3.1+ (patched for CVE-2024-33663 and CVE-2024-33664)
"""

from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
from functools import lru_cache
import os
from typing import Dict, Any

security = HTTPBearer()

# Keycloak configuration
KEYCLOAK_ISSUER = os.getenv(
    "KEYCLOAK_ISSUER",
    "https://auth.guardianinvestmentbd.com/realms/wizardsofts"
)
KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE", "account")
JWKS_URI = f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs"


@lru_cache(maxsize=1)
def get_jwks() -> Dict[str, Any]:
    """
    Fetch JWKS (JSON Web Key Set) from Keycloak

    Cached to avoid repeated network calls.
    Cache is cleared on service restart.

    Returns:
        dict: JWKS containing public keys for token verification

    Raises:
        HTTPException: If JWKS fetch fails
    """
    try:
        response = requests.get(JWKS_URI, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch JWKS from Keycloak: {str(e)}"
        )


def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """
    Verify JWT token from Authorization header

    Validates:
    - Signature (using JWKS from Keycloak)
    - Expiration (exp claim)
    - Issuer (iss claim must match KEYCLOAK_ISSUER)
    - Audience (aud claim must match KEYCLOAK_AUDIENCE)

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        dict: Decoded token payload containing user information

    Raises:
        HTTPException: 401 if token is invalid, expired, or signature fails
        HTTPException: 503 if JWKS fetch fails

    Example:
        @app.get("/protected")
        async def protected_route(token: dict = Security(verify_jwt)):
            user_id = token.get("sub")
            return {"user_id": user_id}
    """
    token = credentials.credentials

    try:
        # Get JWKS (cached)
        jwks = get_jwks()

        # Decode and verify token
        # python-jose 3.3.1+ includes fixes for CVE-2024-33663 (algorithm confusion)
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            issuer=KEYCLOAK_ISSUER,
            audience=KEYCLOAK_AUDIENCE,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            }
        )

        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Token validation error: {str(e)}"
        )


def get_current_user(token_payload: Dict[str, Any] = Security(verify_jwt)) -> Dict[str, Any]:
    """
    Extract user information from validated JWT token

    Args:
        token_payload: Decoded JWT payload from verify_jwt()

    Returns:
        dict: User information including:
            - sub: User ID (UUID)
            - email: User email address
            - preferred_username: Username
            - roles: List of realm roles
            - tenant_id: Tenant identifier (if multi-tenant)

    Example:
        @app.post("/api/v1/signals/generate")
        async def generate_signal(
            request: SignalRequest,
            user: dict = Security(get_current_user)
        ):
            print(f"Signal request from: {user['email']}")
            # ... generate signal
    """
    return {
        "sub": token_payload.get("sub"),
        "email": token_payload.get("email"),
        "preferred_username": token_payload.get("preferred_username"),
        "roles": token_payload.get("realm_access", {}).get("roles", []),
        "tenant_id": token_payload.get("tenant_id"),
    }
