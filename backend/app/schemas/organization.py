from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    created_at: datetime


class UserCreate(BaseModel):
    department_id: str | None = None
    display_name: str = Field(min_length=1, max_length=80)
    role: str = Field(default="employee", pattern="^(admin|employee)$")


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    department_id: str | None
    display_name: str
    role: str
    is_active: bool
    created_at: datetime


class ProjectCreate(BaseModel):
    department_id: str
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    created_by: str
    member_ids: list[str] = Field(default_factory=list)


class ProjectRead(BaseModel):
    id: str
    department_id: str
    name: str
    description: str
    summary: str
    created_by: str | None
    member_ids: list[str]
    created_at: datetime
    updated_at: datetime


class ProjectMemberAssign(BaseModel):
    user_id: str
    assigned_by: str
