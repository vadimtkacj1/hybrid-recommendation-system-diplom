from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.user import User

MAX_MESSAGE_LENGTH = 2000


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_direct_message(db: Session, sender: User, receiver_id: str, content: str) -> Message | None:
    receiver_id = receiver_id.strip()
    content = content.strip()
    if not receiver_id or not content or len(content) > MAX_MESSAGE_LENGTH:
        return None
    receiver = get_user_by_id(db, receiver_id)
    if not receiver:
        return None
    msg = Message(
        id=str(uuid.uuid4()),
        sender_id=sender.id,
        receiver_id=receiver_id,
        content=content,
        created_at=datetime.utcnow(),
    )
    db.add(msg)
    db.commit()
    return msg


def message_to_ws_payload(msg: Message, sender: User) -> dict:
    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "sender_name": sender.name,
        "sender_picture": sender.picture_url,
        "receiver_id": msg.receiver_id,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }


def serialize_message_row(m: Message) -> dict:
    return {
        "id": m.id,
        "sender_id": m.sender_id,
        "receiver_id": m.receiver_id,
        "content": m.content,
        "created_at": m.created_at.isoformat(),
        "is_read": m.is_read,
    }


def fetch_conversation(
    db: Session,
    current_user_id: str,
    other_user_id: str,
    *,
    limit: int = 50,
) -> list[dict]:
    msgs = (
        db.query(Message)
        .filter(
            or_(
                and_(Message.sender_id == current_user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == current_user_id),
            )
        )
        .order_by(Message.created_at.asc())
        .limit(limit)
        .all()
    )
    for m in msgs:
        if m.receiver_id == current_user_id and not m.is_read:
            m.is_read = True
    db.commit()
    return [serialize_message_row(m) for m in msgs]


def count_unread_incoming(db: Session, user_id: str) -> int:
    return (
        db.query(Message)
        .filter(Message.receiver_id == user_id, Message.is_read == False)  # noqa: E712
        .count()
    )


def list_conversation_summaries(db: Session, user_id: str) -> list[dict]:
    msgs = (
        db.query(Message)
        .filter(
            or_(
                Message.sender_id == user_id,
                Message.receiver_id == user_id,
            )
        )
        .all()
    )

    peers_seen: dict[str, Message] = {}
    for m in msgs:
        peer_id = m.receiver_id if m.sender_id == user_id else m.sender_id
        prev = peers_seen.get(peer_id)
        if prev is None or (m.created_at, m.id) > (prev.created_at, prev.id):
            peers_seen[peer_id] = m

    if not peers_seen:
        return []

    peer_users = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(list(peers_seen))).all()
    }

    result: list[dict] = []
    for peer_id, last_msg in peers_seen.items():
        peer = peer_users.get(peer_id)
        if not peer:
            continue
        unread = (
            db.query(Message)
            .filter(
                Message.sender_id == peer_id,
                Message.receiver_id == user_id,
                Message.is_read == False,  # noqa: E712
            )
            .count()
        )
        result.append({
            "peer_id": peer_id,
            "peer_name": peer.name,
            "peer_picture": peer.picture_url,
            "last_message": last_msg.content,
            "last_message_at": last_msg.created_at.isoformat(),
            "unread_count": unread,
        })

    result.sort(key=lambda x: x["last_message_at"], reverse=True)
    return result
