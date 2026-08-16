from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import Project, ProjectMember
from app.repositories.organization import get_project, get_user


def require_project_access(session: Session, project_id: str, user_id: str) -> Project:
    project = get_project(session, project_id)
    user = get_user(session, user_id)
    if not project or not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project or user not found")
    if user.role != "admin" and session.get(ProjectMember, (project_id, user_id)) is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User is not assigned to this project")
    return project
