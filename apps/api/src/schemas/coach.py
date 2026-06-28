from datetime import date
from uuid import UUID

from pydantic import BaseModel


class CoachAvailability(BaseModel):
    week_of: date
    slots_total: int
    slots_taken: int
    available: bool


class CreateInquiryIn(BaseModel):
    application_id: UUID | None = None
    source_screen: str
    contact_method: str
    notes: str = ""


class CoachInquiryOut(BaseModel):
    id: UUID
    available_after_create: bool
