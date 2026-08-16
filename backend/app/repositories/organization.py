from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.organization import Department, Project, ProjectMember, User


def list_departments(session: Session) -> list[Department]:
    return list(session.scalars(select(Department).order_by(Department.created_at)))


def list_users(session: Session, department_id: str | None = None) -> list[User]:
    statement = select(User).where(User.is_active.is_(True)).order_by(User.created_at)
    if department_id:
        statement = statement.where(User.department_id == department_id)
    return list(session.scalars(statement))


def get_user(session: Session, user_id: str) -> User | None:
    return session.get(User, user_id)


def get_department(session: Session, department_id: str) -> Department | None:
    return session.get(Department, department_id)


def get_project(session: Session, project_id: str) -> Project | None:
    statement = (
        select(Project).options(selectinload(Project.members)).where(Project.id == project_id)
    )
    return session.scalar(statement)


def list_projects(
    session: Session, user_id: str | None = None, department_id: str | None = None
) -> list[Project]:
    statement = select(Project).options(selectinload(Project.members)).order_by(Project.created_at)
    if user_id:
        statement = statement.join(ProjectMember).where(ProjectMember.user_id == user_id)
    if department_id:
        statement = statement.where(Project.department_id == department_id)
    return list(session.scalars(statement).unique())
