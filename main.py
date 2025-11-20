import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import create_document, get_documents, db
from schemas import Artwork, Practice, ChatMessage, Booking, ContactMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def create_chat(payload: ChatCreate):
    try:
        inserted_id = create_document("chatmessage", payload)
        return {"id": inserted_id, "message": "Message posted"}
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
