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
