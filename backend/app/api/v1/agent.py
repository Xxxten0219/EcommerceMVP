import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.runtime import run_basic_agent, run_to_read
from app.db.session import get_session
from app.models.agent import AgentRun, ToolCall
from app.schemas.agent import AgentRunCreate, AgentRunRead, ToolCallRead
from app.services.access import require_project_access

router = APIRouter(tags=["agents"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _require_agent_run(session: Session, run_id: str, user_id: str) -> AgentRun:
    run = session.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent Run not found")
    require_project_access(session, run.project_id, user_id)
    return run


@router.post(
    "/conversations/{conversation_id}/agent-runs",
    response_model=AgentRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_run(
    conversation_id: str, payload: AgentRunCreate, session: SessionDependency
) -> AgentRunRead:
    return run_basic_agent(session, conversation_id, payload.user_id, payload.content)


@router.get("/agent-runs/{run_id}", response_model=AgentRunRead)
def get_agent_run(
    run_id: str,
    user_id: Annotated[str, Query()],
    session: SessionDependency,
) -> AgentRunRead:
    return run_to_read(_require_agent_run(session, run_id, user_id))


@router.get("/agent-runs/{run_id}/tool-calls", response_model=list[ToolCallRead])
def get_tool_calls(
    run_id: str,
    user_id: Annotated[str, Query()],
    session: SessionDependency,
) -> list[ToolCallRead]:
    run = _require_agent_run(session, run_id, user_id)
    calls = session.scalars(
        select(ToolCall)
        .where(ToolCall.agent_run_id == run.id)
        .order_by(ToolCall.created_at, ToolCall.id)
    ).all()
    return [
        ToolCallRead(
            id=call.id,
            tool_name=call.tool_name,
            input=json.loads(call.input_json),
            output_summary=(
                json.loads(call.output_summary_json) if call.output_summary_json else None
            ),
            status=call.status,
            duration_ms=call.duration_ms,
            error_message=call.error_message,
            created_at=call.created_at,
        )
        for call in calls
    ]
