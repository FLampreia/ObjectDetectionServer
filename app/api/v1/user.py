import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_user_service
from app.db.database import get_db
from app.exceptions.custom_exceptions import UserNotFound
from app.models.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

user_router = APIRouter()
logger = logging.getLogger(__name__)

@user_router.get("/users", response_model=list[UserRead])
def get_users(service: UserService = Depends(get_user_service)):
    logger.info("Getting users list")
    return service.list_users()

@user_router.get("/users/{user_id}", response_model=UserRead)
def get_user_by_id(user_id: UUID, service: UserService = Depends(get_user_service)):
    logger.info("Getting user with id: %s", user_id)
    user = service.get_user(user_id)
    if not user:
        raise UserNotFound()
    return user

#TODO Update apenas atualiza com todos os campos preenchidos, e a pass nao está encriptada

# @user_router.put("/users/{user_id}", response_model=UserRead)
# def update_user(user_id: UUID, user: UserCreate, service: UserService = Depends(get_user_service)):
#     logger.info("Updating user with id: %s", user_id)
#     updated = service.update_user(user_id, user.username, user.password, user.email, user.full_name)
#     logger.info(f"Updating user with data: %s", user)
#     if not updated:
#         raise UserNotFound()
#     return updated

@user_router.patch("/users/{user_id}", response_model=UserRead)
def update_user_partial(
    user_id: UUID,
    user: UserUpdate,
    service: UserService = Depends(get_user_service),
):

    logger.info("Updating user with id: %s", user_id)

    updated = service.update_user_partial(
        user_id=user_id,
        username=user.username,
        email=user.email,
        password=user.password,
        full_name=user.full_name,
        current_password= user.current_password,
    )

    if not updated:
        raise UserNotFound()

    return updated

@user_router.delete("/users/{user_id}")
def delete_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    logger.info("Deleting user with id: %s", user_id)
    success = service.delete_user(user_id)
    if not success:
        raise UserNotFound()
    return {"success":True}

#TODO ver se os enpoints sem token access tao a funcionar ou nao, perceber o que é RBAC/admin checks. Acho que o otken nao está a funcionar