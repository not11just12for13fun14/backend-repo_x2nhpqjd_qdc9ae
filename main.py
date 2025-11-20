import os
import json
import asyncio
from typing import List, Optional, Dict, Set
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from database import create_document, get_documents, db, update_document_push, get_document_by_id, update_document_pull, update_document_set, delete_document
from schemas import Artwork, Practice, ChatMessage, Booking, ContactMessage, Performance, Room, RoomMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve files saved under /tmp via /static
app.mount("/static", StaticFiles(directory="/tmp"), name="static")

# ---------------------- Simple Role-Based Access Control ----------------------
# Roles: viewer < member < moderator < admin
# Moderation actions require role in {moderator, admin} and a valid admin token.
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

async def get_role(x_role: Optional[str] = Header(default=None), x_admin_token: Optional[str] = Header(default=None)) -> str:
    role = (x_role or "viewer").lower().strip()
    if role in {"moderator", "admin"}:
        if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
            # Downgrade to viewer if token invalid
            return "viewer"
        return role
    if role in {"viewer", "member"}:
        return role
    return "viewer"

async def require_moderator(role: str = Depends(get_role)):
    if role not in {"moderator", "admin"}:
        raise HTTPException(status_code=403, detail="Moderator role required")

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# ---------------------- Artworks API ----------------------
class ArtworkCreate(Artwork):
    pass

@app.get("/artworks")
def list_artworks(limit: Optional[int] = 9):
    """List artworks. Seeds a few samples if collection is empty."""
    try:
        items = get_documents("artwork", {}, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not items:
        # Seed with a few sample digital artworks
        samples: List[ArtworkCreate] = [
            ArtworkCreate(
                title="Glass Prism",
                artist="Studio Nova",
                image_url="https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1600&auto=format&fit=crop",
                description="Light refracting through glass surfaces.",
                tags=["glass", "light", "abstract"],
                year=2023,
            ),
            ArtworkCreate(
                title="Neon Bloom",
                artist="Ari Vega",
                image_url="https://images.unsplash.com/photo-1535905748047-14b0a5499d39?q=80&w=1600&auto=format&fit=crop",
                description="Floral shapes in neon gradients.",
                tags=["neon", "gradient", "flora"],
                year=2022,
            ),
            ArtworkCreate(
                title="Circuit Dreams",
                artist="Kai Ito",
                image_url="https://images.unsplash.com/photo-1518779578993-ec3579fee39f?q=80&w=1600&auto=format&fit=crop",
                description="Microtextures and luminous paths.",
                tags=["tech", "circuit", "futurism"],
                year=2024,
            ),
        ]
        for s in samples:
            try:
                create_document("artwork", s)
            except Exception:
                # Ignore if seeding fails due to env; return empty list
                pass
        try:
            items = get_documents("artwork", {}, limit)
        except Exception:
            items = []

    # Convert ObjectId to string if present
    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["_id"] = str(_id)

    return {"items": items}

@app.post("/artworks", status_code=201)
def create_artwork(payload: ArtworkCreate):
    try:
        inserted_id = create_document("artwork", payload)
        return {"id": inserted_id, "message": "Artwork created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Sustainable Practices API ----------------------
class PracticeCreate(Practice):
    pass

@app.get("/practices")
def list_practices(city: Optional[str] = None, category: Optional[str] = None, limit: Optional[int] = 20):
    """List sustainable practices, optionally filtered by city and/or category."""
    try:
        filt = {}
        if city:
            filt["city"] = city
        if category:
            filt["category"] = category
        items = get_documents("practice", filt, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["_id"] = str(_id)

    return {"items": items}

@app.post("/practices", status_code=201)
def create_practice(payload: PracticeCreate):
    try:
        inserted_id = create_document("practice", payload)
        return {"id": inserted_id, "message": "Practice submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Community Chat API ----------------------
class ChatCreate(ChatMessage):
    pass

@app.get("/chat")
def list_chat(category: Optional[str] = None, limit: Optional[int] = 50):
    """List chat messages, optionally filtered by category/room."""
    try:
        filt = {"category": category} if category else {}
        items = get_documents("chatmessage", filt, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["_id"] = str(_id)

    return {"items": items}

@app.post("/chat", status_code=201)
async def create_chat(payload: ChatCreate):
    try:
        inserted_id = create_document("chatmessage", payload)
        # Broadcast realtime update to chat channel
        data = payload.model_dump()
        data["_id"] = inserted_id
        await hub.broadcast_chat(data.get("category") or "General", {
            "type": "message",
            "item": data,
        })
        return {"id": inserted_id, "message": "Message posted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Moderation endpoints for chat
@app.post("/chat/{message_id}/flag")
def flag_chat_message(message_id: str, _: None = Depends(require_moderator)):
    try:
        ok = update_document_set("chatmessage", message_id, {"flagged": True})
        if not ok:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"message": "Flagged"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/{message_id}")
def delete_chat_message(message_id: str, _: None = Depends(require_moderator)):
    try:
        ok = delete_document("chatmessage", message_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"message": "Deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Workshop Bookings API ----------------------
class BookingCreate(Booking):
    pass

@app.post("/bookings", status_code=201)
def create_booking(payload: BookingCreate):
    try:
        inserted_id = create_document("booking", payload)
        return {"id": inserted_id, "message": "Booking submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bookings")
def list_bookings(limit: Optional[int] = 50):
    try:
        items = get_documents("booking", {}, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["_id"] = str(_id)

    return {"items": items}

# ---------------------- Contact API ----------------------
class ContactCreate(ContactMessage):
    pass

@app.post("/contact", status_code=201)
def create_contact(payload: ContactCreate):
    try:
        inserted_id = create_document("contactmessage", payload)
        return {"id": inserted_id, "message": "Message received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Performances API ----------------------
class PerformanceCreate(Performance):
    pass

@app.get("/performances")
def list_performances(city: Optional[str] = None, discipline: Optional[str] = None, limit: Optional[int] = 50):
    """List live or recorded multidisciplinary performances, with optional filters."""
    try:
        filt = {}
        if city:
            filt["city"] = city
        if discipline:
            filt["discipline"] = discipline
        items = get_documents("performance", filt, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["_id"] = str(_id)

    return {"items": items}

@app.post("/performances", status_code=201)
def create_performance(payload: PerformanceCreate):
    try:
        inserted_id = create_document("performance", payload)
        return {"id": inserted_id, "message": "Performance submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Live Rooms API ----------------------
class RoomCreate(Room):
    pass

@app.post("/rooms", status_code=201)
async def create_room(payload: RoomCreate):
    try:
        inserted_id = create_document("room", payload)
        # Notify room listings channel (optional global broadcast)
        await hub.broadcast_global({"type": "room_created", "id": inserted_id})
        return {"id": inserted_id, "message": "Room created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rooms")
def list_rooms(discipline: Optional[str] = None, status: Optional[str] = None, limit: Optional[int] = 50):
    try:
        filt = {}
        if discipline:
            filt["discipline"] = discipline
        if status:
            filt["status"] = status
        items = get_documents("room", filt, limit)
        for it in items:
            _id = it.get("_id")
            if _id is not None:
                it["_id"] = str(_id)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RoomMessageCreate(RoomMessage):
    pass

@app.post("/rooms/{room_id}/messages", status_code=201)
async def post_room_message(room_id: str, payload: RoomMessageCreate):
    try:
        # Ensure room exists
        room = get_document_by_id("room", room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        # Save message (include room_id from path for consistency)
        data = payload.model_dump()
        data["room_id"] = room_id
        inserted_id = create_document("roommessage", data)
        data["_id"] = inserted_id
        # Broadcast to room subscribers
        await hub.broadcast_room(room_id, {"type": "message", "item": data})
        return {"id": inserted_id, "message": "Message posted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rooms/{room_id}/messages")
def list_room_messages(room_id: str, limit: Optional[int] = 100):
    try:
        items = get_documents("roommessage", {"room_id": room_id}, limit)
        for it in items:
            _id = it.get("_id")
            if _id is not None:
                it["_id"] = str(_id)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rooms/{room_id}/pin", status_code=200)
async def pin_media(room_id: str, url: str = Form(...)):
    try:
        updated = update_document_push("room", room_id, "pinned_media", url)
        if not updated:
            raise HTTPException(status_code=404, detail="Room not found or not updated")
        # Broadcast pin to room subscribers
        await hub.broadcast_room(room_id, {"type": "pin", "url": url})
        return {"message": "Media pinned"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Room moderation
@app.post("/rooms/{room_id}/messages/{message_id}/flag")
def flag_room_message(room_id: str, message_id: str, _: None = Depends(require_moderator)):
    try:
        ok = update_document_set("roommessage", message_id, {"flagged": True})
        if not ok:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"message": "Flagged"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rooms/{room_id}/messages/{message_id}")
def delete_room_message(room_id: str, message_id: str, _: None = Depends(require_moderator)):
    try:
        ok = delete_document("roommessage", message_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"message": "Deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Lightweight Upload Endpoint for Recordings ----------------------
@app.post("/upload", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    """Accept a small file upload and return a pseudo-URL.
    In this ephemeral environment, we'll store to a temp folder and expose a local path as URL.
    """
    try:
        import aiofiles
        upload_dir = "/tmp/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        dest_path = os.path.join(upload_dir, file.filename)
        async with aiofiles.open(dest_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        # Return a pseudo URL; frontend can treat it as downloadable link
        return {"url": f"/static/uploads/{file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Realtime Hub (WebSockets) ----------------------
class RealtimeHub:
    def __init__(self) -> None:
        self.chat_channels: Dict[str, Set[WebSocket]] = {}
        self.room_channels: Dict[str, Set[WebSocket]] = {}
        self.global_channels: Set[WebSocket] = set()
        self.lock = asyncio.Lock()

    async def connect_chat(self, category: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.chat_channels.setdefault(category, set()).add(websocket)
        await self.broadcast_chat(category, {"type": "presence", "event": "join", "count": self.count_chat(category)})

    async def disconnect_chat(self, category: str, websocket: WebSocket):
        async with self.lock:
            conns = self.chat_channels.get(category)
            if conns and websocket in conns:
                conns.remove(websocket)
                if not conns:
                    self.chat_channels.pop(category, None)
        await self.broadcast_chat(category, {"type": "presence", "event": "leave", "count": self.count_chat(category)})

    async def broadcast_chat(self, category: str, message: dict):
        conns = list(self.chat_channels.get(category, set()))
        dead = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        if dead:
            async with self.lock:
                for ws in dead:
                    self.chat_channels.get(category, set()).discard(ws)

    def count_chat(self, category: str) -> int:
        return len(self.chat_channels.get(category, set()))

    async def connect_room(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.room_channels.setdefault(room_id, set()).add(websocket)
        await self.broadcast_room(room_id, {"type": "presence", "event": "join", "count": self.count_room(room_id)})

    async def disconnect_room(self, room_id: str, websocket: WebSocket):
        async with self.lock:
            conns = self.room_channels.get(room_id)
            if conns and websocket in conns:
                conns.remove(websocket)
                if not conns:
                    self.room_channels.pop(room_id, None)
        await self.broadcast_room(room_id, {"type": "presence", "event": "leave", "count": self.count_room(room_id)})

    async def broadcast_room(self, room_id: str, message: dict):
        conns = list(self.room_channels.get(room_id, set()))
        dead = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        if dead:
            async with self.lock:
                for ws in dead:
                    self.room_channels.get(room_id, set()).discard(ws)

    def count_room(self, room_id: str) -> int:
        return len(self.room_channels.get(room_id, set()))

    async def broadcast_global(self, message: dict):
        # Placeholder for future: currently not used by frontend
        conns = list(self.global_channels)
        dead = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        if dead:
            async with self.lock:
                for ws in dead:
                    self.global_channels.discard(ws)

hub = RealtimeHub()

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket, category: Optional[str] = None):
    cat = category or "General"
    await hub.connect_chat(cat, websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
            except Exception:
                continue
            if isinstance(data, dict):
                t = data.get("type")
                if t == "typing":
                    author = data.get("author") or "Anon"
                    await hub.broadcast_chat(cat, {"type": "typing", "author": author})
                elif t == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        await hub.disconnect_chat(cat, websocket)

@app.websocket("/ws/rooms/{room_id}")
async def ws_room(websocket: WebSocket, room_id: str):
    await hub.connect_room(room_id, websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
            except Exception:
                continue
            if isinstance(data, dict):
                t = data.get("type")
                if t == "typing":
                    author = data.get("author") or "Anon"
                    await hub.broadcast_room(room_id, {"type": "typing", "author": author})
                elif t == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        await hub.disconnect_room(room_id, websocket)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
