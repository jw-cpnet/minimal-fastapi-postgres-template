from fastapi import Depends
from fastapi_keycloak_middleware import FastApiUser, get_user

from app.core.app import create_app
from app.core.logging import setup_logging

# Setup logging
setup_logging()

# Create FastAPI application
app = create_app()


@app.get("/")
async def root(user: FastApiUser = Depends(get_user)):
    return {"message": f"Hello, {user.display_name}!"}
