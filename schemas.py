"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Digital art gallery schema
class Artwork(BaseModel):
    """
    Artwork collection schema
    Collection name: "artwork"
    """
    title: str = Field(..., description="Artwork title")
    artist: str = Field(..., description="Artist name")
    image_url: HttpUrl = Field(..., description="Public image URL of the artwork")
    description: Optional[str] = Field(None, description="Short description or concept")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for filtering/search")
    year: Optional[int] = Field(None, ge=1000, le=3000, description="Year created")

# Sustainable practice submission schema
class Practice(BaseModel):
    """
    Sustainable practice submissions
    Collection name: "practice"
    """
    title: str = Field(..., description="Name of the sustainable practice")
    city: str = Field(..., description="City where the practice is implemented")
    description: Optional[str] = Field(None, description="Details of the initiative")
    category: Optional[str] = Field(None, description="Category (e.g., transport, energy, waste)")
    tags: Optional[List[str]] = Field(default_factory=list, description="Keywords for discovery")
    impact_score: Optional[int] = Field(None, ge=1, le=5, description="Estimated impact (1-5)")
    source_url: Optional[HttpUrl] = Field(None, description="Reference or official link")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude for map view")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude for map view")

# Realtime chat-like message (stored in DB)
class ChatMessage(BaseModel):
    """
    Community chat messages
    Collection name: "chatmessage" -> "chatmessage" automatically
    """
    author: str = Field(..., description="Display name of the sender")
    avatar: Optional[HttpUrl] = Field(None, description="Avatar image URL")
    text: Optional[str] = Field(None, description="Message text content")
    media_urls: List[HttpUrl] = Field(default_factory=list, description="Attached media URLs (images/videos/artworks)")
    category: Optional[str] = Field(None, description="Optional category or room name")
    flagged: Optional[bool] = Field(False, description="Whether message is flagged")

# Workshop booking schema
class Booking(BaseModel):
    """
    Workshop booking requests
    Collection name: "booking"
    """
    name: str = Field(..., description="Participant name")
    email: str = Field(..., description="Contact email")
    topic: Optional[str] = Field(None, description="Workshop topic or interest area")
    preferred_date: Optional[str] = Field(None, description="Preferred date (ISO string or text)")
    message: Optional[str] = Field(None, description="Additional notes")

# Contact message schema
class ContactMessage(BaseModel):
    """
    Contact page submissions
    Collection name: "contactmessage"
    """
    name: str = Field(..., description="Sender name")
    email: str = Field(..., description="Sender email")
    subject: Optional[str] = Field(None, description="Subject line")
    message: str = Field(..., description="Message body")

# Multidisciplinary live performance schema
class Performance(BaseModel):
    """
    Multidisciplinary art performance submissions
    Collection name: "performance"
    """
    title: str = Field(..., description="Performance title")
    artist: str = Field(..., description="Lead artist or group")
    discipline: Optional[str] = Field(None, description="Discipline or category (e.g., Dance, Music, Theater)")
    city: Optional[str] = Field(None, description="City of the performance")
    scheduled_at: Optional[str] = Field(None, description="Scheduled date/time (ISO string or free text)")
    live_url: Optional[HttpUrl] = Field(None, description="Live stream URL (YouTube, Twitch, etc.)")
    recording_urls: List[HttpUrl] = Field(default_factory=list, description="Links to recorded media")
    description: Optional[str] = Field(None, description="Overview of the performance")
    tags: Optional[List[str]] = Field(default_factory=list, description="Keywords for discovery")

# Live Rooms for sessions
class Room(BaseModel):
    """
    Live session rooms
    Collection name: "room"
    """
    title: str = Field(..., description="Room title")
    discipline: Optional[str] = Field(None, description="Discipline or theme")
    pinned_media: List[HttpUrl] = Field(default_factory=list, description="Pinned media URLs for the session")
    status: Optional[str] = Field("open", description="Room status: open/closed")

class RoomMessage(BaseModel):
    """
    Messages posted inside a room
    Collection name: "roommessage"
    """
    room_id: str = Field(..., description="Target room id")
    author: str = Field(..., description="Sender display name")
    avatar: Optional[HttpUrl] = Field(None, description="Avatar image URL")
    text: Optional[str] = Field(None, description="Message text")
    media_urls: List[HttpUrl] = Field(default_factory=list, description="Attached media URLs")
    flagged: Optional[bool] = Field(False, description="Whether message is flagged")
