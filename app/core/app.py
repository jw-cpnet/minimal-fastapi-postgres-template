from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi_keycloak_middleware import setup_keycloak_middleware

from app.api.api_router import api_router
from app.core.auth import custom_user_mapper, get_keycloak_config
from app.core.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="minimal fastapi postgres template with Keycloak",
        version="7.0.0",
        description="https://github.com/jw-cpnet/minimal-fastapi-keycloak-template",
        openapi_url="/openapi.json",
        docs_url="/docs",
    )

    # Add Keycloak middleware
    fastapi_logger.debug("Setting up Keycloak middleware")
    setup_keycloak_middleware(
        app,
        keycloak_configuration=get_keycloak_config(),
        add_swagger_auth=True,
        swagger_auth_scopes=["openid", "profile", "email"],
        exclude_patterns=["/openapi.json", "/docs"],
        user_mapper=custom_user_mapper,
    )
    fastapi_logger.debug("Keycloak middleware setup complete")

    # Include routers
    app.include_router(api_router)

    # Add middlewares
    setup_middlewares(app)

    return app

def setup_middlewares(app: FastAPI) -> None:
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
