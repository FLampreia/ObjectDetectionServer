import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_user_service
from app.core.token import get_current_user
from app.db.database import get_db
from app.exceptions.custom_exceptions import UserNotFound, NotAllowedToUpdate, NotAllowedToDelete
from app.models.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

user_router = APIRouter()
logger = logging.getLogger(__name__)

@user_router.get("/users", response_model=list[UserRead])
def get_users(
        service: UserService = Depends(get_user_service),
        current_user = Depends(get_current_user)
):
    logger.info("Getting users list")
    return service.list_users()

@user_router.get("/users/{user_id}", response_model=UserRead)
def get_user_by_id(
        user_id: UUID, service: UserService = Depends(get_user_service),
        current_user = Depends(get_current_user)
 ):
    logger.info("Getting user with id: %s", user_id)
    user = service.get_user(user_id)
    if not user:
        raise UserNotFound()
    return user

@user_router.patch("/users/{user_id}", response_model=UserRead)
def update_user_partial(
        user_id: UUID,
        user: UserUpdate,
        service: UserService = Depends(get_user_service),
        current_user = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise NotAllowedToUpdate()

    logger.info("Updating user with id: %s", user_id)

    updated = service.update_user_partial(
        user_id=user_id,
        username=user.username,
        password=user.password,
        full_name=user.full_name,
        current_password= user.current_password,
    )

    return updated

@user_router.delete("/users/{user_id}")
def delete_user(
        user_id: UUID, service: UserService = Depends(get_user_service),
        current_user = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise NotAllowedToDelete()

    logger.info("Deleting user with id: %s", user_id)
    success = service.delete_user(user_id)
    if not success:
        raise UserNotFound()
    return {"success":True}

