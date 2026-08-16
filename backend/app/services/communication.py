import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.common import utc_now
from app.models.communication import Conversation, Message
from app.repositories.communication import get_conversation, list_messages
from app.schemas.communication import ContextMessage, ContextSnapshot
from app.services.access import require_project_access


def require_conversation_access(
    session: Session, conversation_id: str, user_id: str
) -> Conversation:
    conversation = get_conversation(session, conversation_id)
    if not conversation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    require_project_access(session, conversation.project_id, user_id)
    return conversation


def create_conversation(
    session: Session, project_id: str, user_id: str, title: str
) -> Conversation:
    require_project_access(session, project_id, user_id)
    conversation = Conversation(project_id=project_id, created_by=user_id, title=title.strip())
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def rename_conversation(
    session: Session, conversation_id: str, user_id: str, title: str
) -> Conversation:
    conversation = require_conversation_access(session, conversation_id, user_id)
    conversation.title = title.strip()
    conversation.updated_at = utc_now()
    session.commit()
    session.refresh(conversation)
    return conversation


def create_user_message(
    session: Session, conversation_id: str, user_id: str, content: str
) -> Message:
    conversation = require_conversation_access(session, conversation_id, user_id)
    message = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="user",
        content=content.strip(),
    )
    conversation.updated_at = utc_now()
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def build_context_snapshot(
    session: Session, conversation_id: str, user_id: str, limit: int = 12
) -> ContextSnapshot:
    conversation = require_conversation_access(session, conversation_id, user_id)
    project = require_project_access(session, conversation.project_id, user_id)
    try:
        structured_scope = json.loads(project.structured_scope_json)
    except json.JSONDecodeError:
        structured_scope = {}
    messages = list_messages(session, conversation_id, limit)
    return ContextSnapshot(
        project_id=project.id,
        conversation_id=conversation.id,
        project_summary=project.summary,
        structured_scope=structured_scope,
        recent_messages=[
            ContextMessage(
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
            for message in messages
        ],
    )
