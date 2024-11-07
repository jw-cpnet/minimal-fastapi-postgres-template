import logging
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.logger import logger as fastapi_logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi_keycloak_middleware import (
    FastApiUser,
    KeycloakConfiguration,
    get_user,
    setup_keycloak_middleware,
)

from app.api.api_router import api_router
from app.core.config import get_settings

logging.basicConfig(level=logging.DEBUG)
fastapi_logger.setLevel(logging.DEBUG)

# Create a file handler
file_handler = logging.FileHandler("fastapi_debug.log")
file_handler.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatting configuration
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
fastapi_logger.addHandler(file_handler)
fastapi_logger.addHandler(console_handler)

logging.getLogger("fastapi_keycloak_middleware").setLevel(logging.DEBUG)

# Set up Keycloak configuration
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
    f"Keycloak config: URL={keycloak_config.url}, Realm={keycloak_config.realm}, Client ID={keycloak_config.client_id}, Swagger Client ID={keycloak_config.swagger_client_id}"
)

app = FastAPI(
    title="minimal fastapi postgres template with Keycloak",
    version="7.0.0",
    description="https://github.com/jw-cpnet/minimal-fastapi-keycloak-template",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

# Add this after the keycloak_config definition but before setup_keycloak_middleware


async def custom_user_mapper(userinfo: dict[str, Any]) -> FastApiUser:
    user = FastApiUser(
        first_name=userinfo.get("given_name", ""),
        last_name=userinfo.get("family_name", ""),
        user_id=userinfo["sub"],  # This is the unique user ID from Keycloak
    )
    # Add email as a custom attribute
    setattr(user, "email", userinfo.get("email", ""))
    return user


# Add Keycloak middleware
fastapi_logger.debug("Setting up Keycloak middleware")
setup_keycloak_middleware(
    app,
    keycloak_configuration=keycloak_config,
    add_swagger_auth=True,
    swagger_auth_scopes=["openid", "profile", "email"],
    exclude_patterns=["/openapi.json", "/docs"],
    user_mapper=custom_user_mapper,
)
fastapi_logger.debug("Keycloak middleware setup complete")

app.include_router(api_router)

# Sets all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        str(origin).rstrip("/")
        for origin in get_settings().security.backend_cors_origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Guards against HTTP Host Header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=get_settings().security.allowed_hosts,
)


@app.get("/")
async def root(user: FastApiUser = Depends(get_user)):
    return {"message": f"Hello, {user.display_name}!"}


# After setting up the app and middleware
openapi_schema = get_openapi(
    title=app.title,
    version=app.version,
    routes=app.routes,
)
fastapi_logger.debug(f"OpenAPI Schema: {openapi_schema}")
