from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.clinic import PolyclinicResponse


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"


class HealthCondition(str, Enum):
    DIABETES = "Diabetes"
    HYPERTENSION = "Hypertension"
    HIGH_CHOLESTEROL = "High Cholesterol"


class UserBase(BaseModel):
    nric: str = Field(..., pattern=r"[STFGM]\d{7}[A-Z]")
    first_name: str
    last_name: str
    email: EmailStr
    date_of_birth: date
    gender: Gender
    health_conditions: Optional[List[HealthCondition]] = None

    @field_validator("first_name", "last_name", mode="before")
    def auto_capitalize(cls, value: str) -> str:
        return value.capitalize()


class BookingSlotBase(BaseModel):
    id: UUID
    datetime: datetime
    polyclinic: PolyclinicResponse
