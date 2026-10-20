from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..ws_manager import manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/deck")
async def deck_ws(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            # Clients don't need to send anything; we just keep the socket
            # open and use it to receive broadcasts. Reading here lets us
            # detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
