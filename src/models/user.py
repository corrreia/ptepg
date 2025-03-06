from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# Base model with common fields
class UserBase(BaseModel):
    username: str
    email: EmailStr  # Ensures valid email format
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# Model for user data retrieved from the database
class User(UserBase):
    id: str  # Using str to be compatible with both SQL and MongoDB
    created_at: datetime
    updated_at: datetime
