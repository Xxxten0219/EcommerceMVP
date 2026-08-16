from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.communication import list_conversations, list_messages
from app.schemas.communication import (
    ContextSnapshot,
    ConversationCreate,
    ConversationRead,
    ConversationRename,
    MessageCreate,
    MessageRead,
)
from app.services.access import require_project_access
from app.services.communication import (
    build_context_snapshot,
    create_conversation,
    create_user_message,
    rename_conversation,
    require_conversation_access,
)

router = APIRouter(tags=["conversations"])
SessionDependency = Annotated[Session, Depends(get_session)]


def conversation_read(item) -> ConversationRead:
    return ConversationRead(
        id=item.id,
        project_id=item.project_id,
        created_by=item.created_by,
        title=item.title,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def message_read(item) -> MessageRead:
    return MessageRead(
        id=item.id,
        conversation_id=item.conversation_id,
        user_id=item.user_id,
        role=item.role,
        content=item.content,
        metadata_json=item.metadata_json,
        created_at=item.created_at,
    )


@router.get("/projects/{project_id}/conversations", response_model=list[ConversationRead])
def conversations(
    project_id: str, user_id: Annotated[str, Query()], session: SessionDependency
) -> list[ConversationRead]:
    require_project_access(session, project_id, user_id)
    return [conversation_read(item) for item in list_conversations(session, project_id)]


@router.post(
    "/projects/{project_id}/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def add_conversation(
    project_id: str, payload: ConversationCreate, session: SessionDependency
) -> ConversationRead:
    return conversation_read(
        create_conversation(session, project_id, payload.user_id, payload.title)
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationRead)
def update_conversation(
    conversation_id: str, payload: ConversationRename, session: SessionDependency
) -> ConversationRead:
    return conversation_read(
        rename_conversation(session, conversation_id, payload.user_id, payload.title)
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
def messages(
    conversation_id: str,
    user_id: Annotated[str, Query()],
    session: SessionDependency,
) -> list[MessageRead]:
    require_conversation_access(session, conversation_id, user_id)
    return [message_read(item) for item in list_messages(session, conversation_id)]


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
def add_message(
    conversation_id: str, payload: MessageCreate, session: SessionDependency
) -> MessageRead:
    return message_read(
        create_user_message(session, conversation_id, payload.user_id, payload.content)
    )


@router.get("/conversations/{conversation_id}/context", response_model=ContextSnapshot)
def context(
    conversation_id: str,
    user_id: Annotated[str, Query()],
    session: SessionDependency,
) -> ContextSnapshot:
    return build_context_snapshot(session, conversation_id, user_id)
