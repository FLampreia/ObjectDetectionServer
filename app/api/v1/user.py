import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.db.database import SessionLocal
from app.models.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter()
logger = logging.getLogger(__name__)

def get_user_service() -> UserService:
    return UserService(session=SessionLocal())

@router.get("/users", response_model=list[UserRead])
def get_users(service: UserService = Depends(get_user_service)):
    logger.info("Getting users list")
    return service.list_users()


@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    logger.info("Creating user with data: %s", user)
    return service.create_user(user.username, user.password, user.email, user.full_name)

@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    logger.info("Getting user with id: %s", user_id)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

#TODO  Update apenas atualiza com todos os campos preenchidos, e a pass nao está encriptada

@router.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, user: UserCreate, service: UserService = Depends(get_user_service)):
    logger.info("Updating user with id: %s", user_id)
    updated = service.update_user(user_id, user.username, user.password, user.email, user.full_name)
    logger.info(f"Updating user with data: %s", user)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.delete("/users/{user_id}")
def delete_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    logger.info("Deleting user with id: %s", user_id)
    success = service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success":True}