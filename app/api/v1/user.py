from fastapi import APIRouter, Depends, HTTPException

from app.db.database import SessionLocal
from app.models.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter()

def get_user_service() -> UserService:
    return UserService(session=SessionLocal())

@router.get("/users", response_model=list[UserRead])
def get_users(service: UserService = Depends(get_user_service)):
    return service.list_users()


@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    return service.create_user(user.username, user.password, user.email, user.full_name)
