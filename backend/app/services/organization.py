from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Project, ProjectMember, User
from app.repositories.organization import get_department, get_project, get_user
from app.schemas.organization import ProjectCreate, ProjectRead, UserCreate


def project_to_read(project: Project) -> ProjectRead:
    return ProjectRead(
        id=project.id,
        department_id=project.department_id,
        name=project.name,
        description=project.description,
        summary=project.summary,
        created_by=project.created_by,
        member_ids=[member.user_id for member in project.members],
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def create_user(session: Session, payload: UserCreate) -> User:
    if payload.department_id and not get_department(session, payload.department_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Department not found")
    if payload.role == "employee" and not payload.department_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Employee requires a department")

    user = User(**payload.model_dump())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_project(session: Session, payload: ProjectCreate) -> Project:
    department = get_department(session, payload.department_id)
    creator = get_user(session, payload.created_by)
    if not department or not creator:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Department or creator not found")
    if creator.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only demo administrators create projects")

    member_ids = list(dict.fromkeys(payload.member_ids))
    members = (
        list(session.scalars(select(User).where(User.id.in_(member_ids)))) if member_ids else []
    )
    if len(members) != len(member_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "One or more members do not exist")
    if any(member.department_id != payload.department_id for member in members):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Member must belong to project department")

    project = Project(
        department_id=payload.department_id,
        name=payload.name,
        description=payload.description,
        created_by=payload.created_by,
    )
    session.add(project)
    session.flush()
    for member in members:
        session.add(
            ProjectMember(
                project_id=project.id,
                user_id=member.id,
                assigned_by=payload.created_by,
            )
        )
    session.commit()
    return get_project(session, project.id)  # type: ignore[return-value]


def assign_project_member(
    session: Session, project_id: str, user_id: str, assigned_by: str
) -> Project:
    project = get_project(session, project_id)
    user = get_user(session, user_id)
    assigner = get_user(session, assigned_by)
    if not project or not user or not assigner:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project or user not found")
    if assigner.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only demo administrators assign projects")
    if user.department_id != project.department_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Member must belong to project department")
    if session.get(ProjectMember, (project_id, user_id)) is None:
        session.add(ProjectMember(project_id=project_id, user_id=user_id, assigned_by=assigned_by))
        session.commit()
    return get_project(session, project_id)  # type: ignore[return-value]


def remove_project_member(session: Session, project_id: str, user_id: str) -> None:
    member = session.get(ProjectMember, (project_id, user_id))
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project membership not found")
    session.delete(member)
    session.commit()
