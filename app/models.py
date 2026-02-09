"""
Pydantic Models for Runner Platform
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime


class RunnerApplicationCreate(BaseModel):
    """Schema per creare una nuova richiesta"""
    
    name: str = Field(..., min_length=2, max_length=100, description="Nome completo")
    email: EmailStr = Field(..., description="Email valida")
    age: int = Field(..., ge=18, le=100, description="Età (18-100)")
    
    level: Literal["beginner", "intermediate", "advanced"] = Field(
        ..., 
        description="Livello running"
    )
    
    goal: Literal["5k", "10k", "half_marathon", "marathon", "fitness"] = Field(
        ...,
        description="Obiettivo principale"
    )
    
    availability: List[str] = Field(
        ...,
        min_length=1,
        description="Giorni/orari disponibili"
    )
    
    dublin_zone: Literal[
        "city_centre",
        "northside", 
        "southside",
        "docklands",
        "phoenix_park",
        "coastal",
        "any"
    ] = Field(..., description="Zona preferita di Dublino")
    
    experience: Optional[str] = Field(
        None,
        max_length=500,
        description="Esperienza precedente con gruppi running"
    )
    
    current_pace: Optional[str] = Field(
        None,
        max_length=20,
        description="Ritmo attuale (es: 5:30 min/km)"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida che il nome non sia solo spazi"""
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    @field_validator('availability')
    @classmethod
    def validate_availability(cls, v: List[str]) -> List[str]:
        """Valida che ci sia almeno una disponibilità"""
        if not v:
            raise ValueError("At least one availability slot required")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mario Rossi",
                "email": "mario@example.com",
                "age": 35,
                "level": "intermediate",
                "goal": "half_marathon",
                "availability": ["monday_evening", "saturday_morning"],
                "dublin_zone": "southside",
                "experience": "Ho corso per 2 anni con un gruppo",
                "current_pace": "5:30"
            }
        }


class RunnerApplication(RunnerApplicationCreate):
    """Schema completo con metadata (per response)"""
    
    id: str = Field(..., description="ID univoco")
    created_at: datetime = Field(..., description="Data creazione")
    status: Literal["pending", "approved", "rejected"] = Field(
        default="pending",
        description="Status richiesta"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123xyz",
                "name": "Mario Rossi",
                "email": "mario@example.com",
                "age": 35,
                "level": "intermediate",
                "goal": "half_marathon",
                "availability": ["monday_evening", "saturday_morning"],
                "dublin_zone": "southside",
                "experience": "Ho corso per 2 anni",
                "current_pace": "5:30",
                "created_at": "2024-02-06T10:00:00Z",
                "status": "pending"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: Literal["healthy", "unhealthy"]
    message: str
    version: str
    timestamp: Optional[datetime] = None
