from fastapi import APIRouter, Depends
from fastapi_keycloak_middleware import FastApiUser, get_user

from app.schemas.responses import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse, description="Get current user")
async def read_current_user(
    current_user: FastApiUser = Depends(get_user),
) -> FastApiUser:
    return current_user
