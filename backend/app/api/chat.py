from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.auth import AuthService
from app.services.chat import ConnectionManager, get_chat_connection_manager
from app.services.chat import messages as chat_messages

router = APIRouter()

__all__ = ["router", "ConnectionManager"]


@router.websocket("/ws")
async def chat_ws(
    ws: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    auth = AuthService()
    current_user = auth.verify_token(token, db)
    if not current_user:
        await ws.close(code=4001)
        return

    manager = get_chat_connection_manager()
    await manager.connect(current_user.id, ws)
    try:
        while True:
            data = await ws.receive_json()
            receiver_id = data.get("receiver_id", "").strip()
            content = data.get("content", "").strip()
            if not receiver_id or not content:
                continue
            if len(content) > chat_messages.MAX_MESSAGE_LENGTH:
                continue

            msg = chat_messages.create_direct_message(db, current_user, receiver_id, content)
            if not msg:
                continue

            payload = chat_messages.message_to_ws_payload(msg, current_user)
            await manager.send_to_user(current_user.id, payload)
            await manager.send_to_user(msg.receiver_id, payload)

    except WebSocketDisconnect:
        manager.disconnect(current_user.id, ws)


@router.get("/messages/{other_user_id}")
def get_conversation(
    other_user_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not chat_messages.get_user_by_id(db, other_user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return chat_messages.fetch_conversation(db, current_user.id, other_user_id, limit=limit)


@router.get("/unread-count")
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"unread": chat_messages.count_unread_incoming(db, current_user.id)}


@router.get("/conversations")
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return chat_messages.list_conversation_summaries(db, current_user.id)
