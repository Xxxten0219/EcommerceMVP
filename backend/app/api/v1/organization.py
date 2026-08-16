from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.organization import list_departments, list_projects, list_users
from app.schemas.organization import (
    DepartmentRead,
    ProjectCreate,
    ProjectMemberAssign,
    ProjectRead,
    UserCreate,
    UserRead,
)
from app.services.organization import (
    assign_project_member,
    create_project,
    create_user,
    project_to_read,
    remove_project_member,
)

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/departments", response_model=list[DepartmentRead], tags=["organization"])
def departments(session: SessionDependency) -> list[DepartmentRead]:
    return [DepartmentRead.model_validate(item) for item in list_departments(session)]


@router.get("/users", response_model=list[UserRead], tags=["organization"])
def users(
    session: SessionDependency, department_id: Annotated[str | None, Query()] = None
) -> list[UserRead]:
    return [UserRead.model_validate(item) for item in list_users(session, department_id)]


@router.post(
    "/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["organization"]
)
def add_user(payload: UserCreate, session: SessionDependency) -> UserRead:
    return UserRead.model_validate(create_user(session, payload))


@router.get("/projects", response_model=list[ProjectRead], tags=["projects"])
def projects(
    session: SessionDependency,
    user_id: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
) -> list[ProjectRead]:
    return [
        project_to_read(item)
        for item in list_projects(session, user_id=user_id, department_id=department_id)
    ]


@router.post(
    "/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    tags=["projects"],
)
def add_project(payload: ProjectCreate, session: SessionDependency) -> ProjectRead:
    return project_to_read(create_project(session, payload))


@router.post("/projects/{project_id}/members", response_model=ProjectRead, tags=["projects"])
def add_project_member(
    project_id: str, payload: ProjectMemberAssign, session: SessionDependency
) -> ProjectRead:
    return project_to_read(
        assign_project_member(session, project_id, payload.user_id, payload.assigned_by)
    )


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["projects"],
)
def delete_project_member(project_id: str, user_id: str, session: SessionDependency) -> Response:
    remove_project_member(session, project_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
