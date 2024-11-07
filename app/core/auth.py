from typing import Any

from fastapi.logger import logger as fastapi_logger
from fastapi_keycloak_middleware import FastApiUser, KeycloakConfiguration

from app.core.config import get_settings


def get_keycloak_config() -> KeycloakConfiguration:
    keycloak_config = KeycloakConfiguration(
        url=get_settings().keycloak.server_url,
        realm=get_settings().keycloak.realm,
        client_id=get_settings().keycloak.client_id,
        client_secret=get_settings().keycloak.client_secret,
        swagger_client_id=get_settings().keycloak.swagger_client_id,
        verify=False,
        audience=["account", "api"],
    )

    fastapi_logger.debug(
        f"Keycloak config: URL={keycloak_config.url}, "
        f"Realm={keycloak_config.realm}, "
        f"Client ID={keycloak_config.client_id}, "
        f"Swagger Client ID={keycloak_config.swagger_client_id}"
    )

    return keycloak_config

async def custom_user_mapper(userinfo: dict[str, Any]) -> FastApiUser:
    user = FastApiUser(
        first_name=userinfo.get("given_name", ""),
        last_name=userinfo.get("family_name", ""),
        user_id=userinfo["sub"],
    )
    setattr(user, "email", userinfo.get("email", ""))
    return user
