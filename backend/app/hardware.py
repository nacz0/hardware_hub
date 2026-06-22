from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.auth import get_current_user, require_admin
from app.database import (
    create_hardware,
    delete_hardware,
    get_hardware,
    list_hardware,
    transition_hardware_status,
    update_hardware_status,
)


HardwareStatus = Literal["Available", "In Use", "Repair", "Unknown"]

router = APIRouter(tags=["hardware"])


class HardwareCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    external_id: int | None = Field(default=None, alias="externalId")
    name: str = Field(min_length=1)
    brand: str | None = None
    purchase_date: str | None = Field(default=None, alias="purchaseDate")
    status: HardwareStatus = "Available"
    notes: str | None = None
    assigned_to: str | None = Field(default=None, alias="assignedTo")
    history: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Hardware name is required")
        return normalized


def get_hardware_or_404(hardware_id: int) -> dict:
    hardware_item = get_hardware(hardware_id)
    if hardware_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found",
        )
    return hardware_item


def require_hardware_result(hardware_item: dict | None) -> dict:
    if hardware_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found",
        )
    return hardware_item


def reject_invalid_transition(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def rent_available_hardware(hardware_id: int, user_email: str) -> dict:
    hardware_item = get_hardware_or_404(hardware_id)
    if hardware_item["status"] != "Available":
        reject_invalid_transition("Hardware can only be rented when Available")

    updated = transition_hardware_status(
        hardware_id,
        "Available",
        "In Use",
        user_email,
    )
    if updated is None:
        get_hardware_or_404(hardware_id)
        reject_invalid_transition("Hardware can only be rented when Available")
    return require_hardware_result(updated)


def return_in_use_hardware(hardware_id: int) -> dict:
    hardware_item = get_hardware_or_404(hardware_id)
    if hardware_item["status"] != "In Use":
        reject_invalid_transition("Hardware can only be returned when In Use")
    if not str(hardware_item.get("assigned_to") or "").strip():
        reject_invalid_transition("Hardware cannot be returned without an assigned user")

    updated = transition_hardware_status(
        hardware_id,
        "In Use",
        "Available",
        None,
        require_assigned_to=True,
    )
    if updated is None:
        current = get_hardware_or_404(hardware_id)
        if current["status"] != "In Use":
            reject_invalid_transition("Hardware can only be returned when In Use")
        reject_invalid_transition("Hardware cannot be returned without an assigned user")
    return require_hardware_result(updated)


def mark_hardware_status(hardware_id: int, status_value: str) -> dict:
    get_hardware_or_404(hardware_id)
    updated = update_hardware_status(hardware_id, status_value, None)
    return require_hardware_result(updated)


def delete_existing_hardware(hardware_id: int) -> None:
    if not delete_hardware(hardware_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found",
        )


@router.get("/hardware")
def list_hardware_items() -> list[dict]:
    return list_hardware()


@router.post(
    "/hardware",
    status_code=status.HTTP_201_CREATED,
)
def create_hardware_item(
    payload: HardwareCreateRequest,
    _admin: dict = Depends(require_admin),
) -> dict:
    return create_hardware(payload.model_dump())


@router.post("/hardware/{hardware_id}/rent")
def rent_hardware(
    hardware_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return rent_available_hardware(hardware_id, current_user["email"])


@router.post("/hardware/{hardware_id}/return")
def return_hardware(
    hardware_id: int,
    _current_user: dict = Depends(get_current_user),
) -> dict:
    return return_in_use_hardware(hardware_id)


@router.post("/hardware/{hardware_id}/repair")
def mark_hardware_repair(
    hardware_id: int,
    _admin: dict = Depends(require_admin),
) -> dict:
    return mark_hardware_status(hardware_id, "Repair")


@router.post("/hardware/{hardware_id}/available")
def mark_hardware_available(
    hardware_id: int,
    _admin: dict = Depends(require_admin),
) -> dict:
    return mark_hardware_status(hardware_id, "Available")


@router.delete(
    "/hardware/{hardware_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_hardware_item(
    hardware_id: int,
    _admin: dict = Depends(require_admin),
) -> None:
    delete_existing_hardware(hardware_id)
