import uuid

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship

from app.models.database import Base


# Define ORM models (existing tables)
class User(AsyncAttrs, Base):
    __tablename__ = "users"

    id = Column(
        "id",
        String,
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    address_id = Column("address_id", String, ForeignKey("addresses.id"), nullable=True)
    enrolled_clinic_id = Column(
        "enrolled_clinic_id", String, ForeignKey("clinics.id"), nullable=True
    )
    nric = Column("nric", String, unique=True, nullable=False)
    first_name = Column("first_name", String, nullable=False)
    last_name = Column("last_name", String, nullable=False)
    email = Column("email", String, unique=True, nullable=False)
    date_of_birth = Column("date_of_birth", Date, nullable=False)
    gender = Column("gender", String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(
        "created_at", DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    address = relationship("Address", back_populates="users")
    enrolled_clinic = relationship("Clinic", back_populates="users")
    vaccine_records = relationship("VaccineRecord", back_populates="user")


class Clinic(AsyncAttrs, Base):
    __tablename__ = "clinics"

    id = Column(
        "id",
        String,
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    address_id = Column(
        "address_id", String, ForeignKey("addresses.id"), nullable=False
    )
    name = Column("name", String, nullable=False)
    type = Column("type", String, nullable=False)
    created_at = Column(
        "created_at", DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    users = relationship("User", back_populates="enrolled_clinic")
    address = relationship("Address", back_populates="clinic")
    booking_slots = relationship("BookingSlot", back_populates="polyclinic")


class Address(AsyncAttrs, Base):
    __tablename__ = "addresses"

    id = Column(
        "id",
        String,
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    postal_code = Column("postal_code", String, nullable=False)
    address = Column("address", String, nullable=False)
    latitude = Column("latitude", Numeric(9, 6), nullable=False)
    longitude = Column("longitude", Numeric(9, 6), nullable=False)
    created_at = Column(
        "created_at", DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    users = relationship("User", back_populates="address")
    clinic = relationship("Clinic", back_populates="address")


class Vaccine(AsyncAttrs, Base):
    __tablename__ = "vaccines"

    id = Column(
        "id",
        String,
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    name = Column("name", String, unique=True, nullable=False)
    created_at = Column(
        "created_at", DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    booking_slots = relationship("BookingSlot", back_populates="vaccine")
    vaccine_criterias = relationship("VaccineCriteria", back_populates="vaccine")


class VaccineCriteria(AsyncAttrs, Base):
    __tablename__ = "vaccinecriteria"

    id = Column(
        "id",
        String,
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    vaccine_id = Column("vaccine_id", String, ForeignKey("vaccines.id"), nullable=False)
    age_criteria = Column("age_criteria", String)
    gender_criteria = Column("gender_criteria", String)
    health_condition_criteria = Column("health_condition_criteria", String)
    doses_required = Column("doses_required", Integer, nullable=False)
    frequency = Column("frequency", String)
    created_at = Column(
        "created_at", DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    vaccine = relationship("Vaccine", back_populates="vaccine_criterias")


class BookingSlot(AsyncAttrs, Base):
    __tablename__ = "bookingslots"

    id = Column(
        "id",
        String,
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    polyclinic_id = Column(
        "polyclinic_id", String, ForeignKey("clinics.id"), nullable=False
    )
    vaccine_id = Column("vaccine_id", String, ForeignKey("vaccines.id"), nullable=False)
    datetime = Column("datetime", DateTime, nullable=False)
    created_at = Column(
        "created_at", DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    polyclinic = relationship("Clinic", back_populates="booking_slots")
    vaccine = relationship("Vaccine", back_populates="booking_slots")
    vaccine_record = relationship("VaccineRecord", back_populates="booking_slot")


class VaccineRecord(AsyncAttrs, Base):
    __tablename__ = "vaccinerecords"

    id = Column(
        "id",
        String,
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    user_id = Column("user_id", String, ForeignKey("users.id"), nullable=False)
    booking_slot_id = Column(
        "booking_slot_id", String, ForeignKey("bookingslots.id"), nullable=False
    )
    status = Column("status", String, nullable=False)
    created_at = Column(
        "created_at", DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="vaccine_records")
    booking_slot = relationship("BookingSlot", back_populates="vaccine_record")
