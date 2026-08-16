from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Department, Project, ProjectMember, User

DEMO_DEPARTMENTS = [
    ("artwork", "美工部门"),
    ("sales", "销售部门"),
    ("selection", "选品部门"),
]


def seed_demo_organization(session: Session) -> None:
    if session.scalar(select(Department.id).limit(1)):
        return

    departments = [Department(code=code, name=name) for code, name in DEMO_DEPARTMENTS]
    session.add_all(departments)
    session.flush()
    department_by_code = {department.code: department for department in departments}

    admin = User(display_name="演示管理员", role="admin", department_id=None)
    employees = [
        User(
            display_name="林然",
            role="employee",
            department_id=department_by_code["artwork"].id,
        ),
        User(
            display_name="周启",
            role="employee",
            department_id=department_by_code["sales"].id,
        ),
        User(
            display_name="陈禾",
            role="employee",
            department_id=department_by_code["selection"].id,
        ),
    ]
    session.add_all([admin, *employees])
    session.flush()

    project_specs = [
        ("artwork", "龙门架主图优化", "演示商品图版本化编辑流程", employees[0]),
        ("sales", "美国站销售分析", "演示报表导入、校验和销售分析", employees[1]),
        ("selection", "健身器材选品计划", "演示库存压力和补货建议", employees[2]),
    ]
    for code, name, description, employee in project_specs:
        project = Project(
            department_id=department_by_code[code].id,
            name=name,
            description=description,
            created_by=admin.id,
        )
        session.add(project)
        session.flush()
        session.add(ProjectMember(project_id=project.id, user_id=employee.id, assigned_by=admin.id))

    session.commit()
