from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.communication import Conversation, Message


def list_conversations(session: Session, project_id: str) -> list[Conversation]:
    statement = (
        select(Conversation)
        .where(Conversation.project_id == project_id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(session.scalars(statement))


def get_conversation(session: Session, conversation_id: str) -> Conversation | None:
    return session.get(Conversation, conversation_id)


def list_messages(session: Session, conversation_id: str, limit: int = 100) -> list[Message]:
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(reversed(list(session.scalars(statement))))
