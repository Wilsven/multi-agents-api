import pytest
from httpx import AsyncClient
from pydantic import TypeAdapter
from requests import Response

from app.schemas.booking import AvailableSlotResponse, BookingSlotResponse
from app.schemas.record import VaccineRecordResponse
from app.schemas.vaccine import VaccineCriteriaResponse


# ============================================================================
# Authorized user gets all available valid slots
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case, params, expected_status",
    [
        # Basic test with just vaccine name
        (1, {"vaccine_name": "Influenza (INF)"}, 200),
        # Test with specified polyclinic
        (
            2,
            {"vaccine_name": "Influenza (INF)", "polyclinic_name": "yishun polyclinic"},
            200,
        ),
    ],
)
async def test_authorized_user_get_all_available_booking_slots(
    authorized_client: AsyncClient,
    case: int,
    params: dict,
    expected_status: int,
):

    res: Response = await authorized_client.get("/bookings/available", params=params)
    assert res.status_code == expected_status

    slots_data = res.json()
    adapter = TypeAdapter(AvailableSlotResponse)

    match case:
        case 1:
            assert len(slots_data) == 2
            for slot in slots_data:
                # Test for slot data structure compared to our schema
                try:
                    adapter.validate_python(slot)
                except Exception as e:
                    pytest.fail(
                        f"Response data doesn't match AvailableSlotResponse structure: {e}"
                    )
        case 2:
            assert len(slots_data) == 1
            slot = AvailableSlotResponse(**slots_data[0])
            assert slot.polyclinic.name == "Yishun Polyclinic"


# ============================================================================
# Authorized user gets all no available slots
# ============================================================================
@pytest.mark.asyncio
async def test_authorized_user_invalid_get_all_available_booking_slots(
    authorized_client: AsyncClient,
):
    # Test with non-existent vaccine name
    params = {"vaccine_name": "wrongvaccine"}

    res: Response = await authorized_client.get("/bookings/available", params=params)
    assert res.status_code == 404
    assert (
        res.json().get("detail") == f"No available slots for {params['vaccine_name']}."
    )


# ============================================================================
# Unauthorized user gets all slots
# ============================================================================
@pytest.mark.asyncio
async def test_unauthorized_user_get_all_available_booking_slots(
    async_client: AsyncClient,
):
    params = {"vaccine_name": "Influenza (INF)"}
    res: Response = await async_client.get("/bookings/available", params=params)
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


# ============================================================================
# Authorized user gets a valid booking slot
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "slot_id, expected_vaccine",
    [
        # See data.sql for the available slots
        ("97ba51db-48d8-4873-b1ee-57a9b7f766f0", "Influenza (INF)"),
        ("21b89cd2-f99c-4113-bb46-5cc21d566b97", "Human papillomavirus (HPV2 or HPV4)"),
    ],
)
async def test_authorized_user_get_valid_booking_slot(
    authorized_client: AsyncClient, slot_id: str, expected_vaccine: str
):
    res: Response = await authorized_client.get(f"/bookings/{slot_id}")

    assert res.status_code == 200
    slot = BookingSlotResponse(**res.json())
    assert str(slot.id) == slot_id
    assert slot.vaccine.name == expected_vaccine

    for criteria in slot.vaccine.vaccine_criterias:
        assert isinstance(criteria, VaccineCriteriaResponse)
        if slot.vaccine.name == "Influenza (INF)":
            assert criteria.age_criteria in [
                "18-64 years",
            ]
            assert criteria.gender_criteria == "None"

        if slot.vaccine.name == "Human papillomavirus (HPV2 or HPV4)":
            assert criteria.age_criteria in [
                "12-13 years",
                "13-14 years",
                "18-26 years",
            ]
            assert criteria.gender_criteria == "F"


# ============================================================================
# Authorized user gets an invalid booking slot
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "slot_id",
    [
        # See data.sql for the available records
        "b6732344-bc30-4401-9a69-b91e28273b8d",  # vaccine record id, hence invalid
        "invalid-id-2",
    ],
)
async def test_invalid_booking_slot(authorized_client: AsyncClient, slot_id: str):
    res: Response = await authorized_client.get(f"/bookings/{slot_id}")

    assert res.status_code == 404
    assert res.json().get("detail") == f"Slot with booking id {slot_id} not found."


# ============================================================================
# Unauthorized user gets valid/invalid booking slot
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "slot_id",
    [
        # See data.sql for the available slots
        "97ba51db-48d8-4873-b1ee-57a9b7f766f0",  # valid slot ID
        "25db80a6-68ab-43c2-8dc2-6bee617b7827",  # invalid slot ID
    ],
)
async def test_unauthorized_user_get_booking_slot(
    async_client: AsyncClient, slot_id: str
):
    res: Response = await async_client.get(f"/bookings/{slot_id}")
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


# ============================================================================
# Authorized user schedules a valid slot
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "slot_id",
    [
        # See data.sql for the available slots
        "213fa5e7-abbb-4e55-bccc-318db42ace81",
        "e7bbc307-ae75-4854-bd91-d6851ae085fd",
    ],
)
async def test_authorized_user_valid_schedule(
    authorized_client_for_scheduling: AsyncClient, slot_id: str
):
    json_body = {"booking_slot_id": slot_id}
    res: Response = await authorized_client_for_scheduling.post(
        "/bookings/schedule", json=json_body
    )

    assert res.status_code == 201

    booked_slot = VaccineRecordResponse(**res.json())
    assert str(booked_slot.booking_slot_id) == slot_id
    assert (
        str(booked_slot.user_id) == authorized_client_for_scheduling.headers["user_id"]
    )
    assert booked_slot.status.value == "booked"


# ============================================================================
# Authorized user schedules an invalid slot (eihter booked or invalid ID)
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "slot_id, expected_status_code, expected_error_message",
    [
        # Invalid UUID
        (
            "97ba51db-48d8-4873-b1ee-57a9b7f766fa",
            404,
            "Booking slot with slot id 97ba51db-48d8-4873-b1ee-57a9b7f766fa not found.",
        ),
        # Valid ID, booked by other user:
        ("97ba51db-48d8-4873-b1ee-57a9b7f766f0", 400, "Slot already booked."),
        # Invalid ID: 422 Unprocessible Entity
        (
            "invalid-id-3",
            422,
            "Input should be a valid UUID, invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], found `i` at 1",
        ),
    ],
)
async def test_authorized_user_invalid_schedule(
    authorized_client_for_scheduling: AsyncClient,
    slot_id: str,
    expected_status_code: int,
    expected_error_message: str,
):
    json_body = {"booking_slot_id": slot_id}

    res: Response = await authorized_client_for_scheduling.post(
        "/bookings/schedule", json=json_body
    )

    assert res.status_code == expected_status_code

    error_response = res.json()

    # 422 Unprocessable Entity
    if res.status_code == 422:
        error_messages = [error.get("msg") for error in error_response["detail"]]
        assert error_messages[0] == expected_error_message

    # 400 or 404 status codes
    else:
        assert error_response.get("detail") == expected_error_message


# ============================================================================
# Unauthorized user schedules a valid/invalid slot
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "slot_id",
    [
        # See data.sql for the available slots
        "97ba51db-48d8-4873-b1ee-57a9b7f766f0",  # valid slot ID
        "25db80a6-68ab-43c2-8dc2-6bee617b7827",  # invalid slot ID
    ],
)
async def test_unauthorized_user_schedule(async_client: AsyncClient, slot_id: str):

    json_body = {"booking_slot_id": slot_id}
    res: Response = await async_client.post("/bookings/schedule", json=json_body)

    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


# ============================================================================
# Authorized user cancels a valid booking
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "record_id",
    [
        # See data.sql for the available records
        "a6578d08-4e81-40ca-bc30-c9f2d01024aa"
    ],
)
async def test_authorized_user_valid_cancel(
    authorized_client_for_scheduling: AsyncClient, record_id: str
):

    res = await authorized_client_for_scheduling.delete(f"/bookings/cancel/{record_id}")

    assert res.status_code == 200
    assert res.json().get("detail") == "Vaccination slot successfully cancelled."


# ============================================================================
# Authorized user cancels invalid booking
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "record_id, expected_status, expected_detail",
    [
        (
            "b6732344-bc30-4401-9a69-b91e28273b8d",
            401,
            "You are not authorized to cancel this vaccination slot.",
        ),
        (
            "7eb3a1a2-dd8c-4cd7-84d5-cd5621ab4fc2",
            404,
            "Vaccine record with id 7eb3a1a2-dd8c-4cd7-84d5-cd5621ab4fc2 not found.",
        ),
        ("invalid-id-4", 404, "Vaccine record with id invalid-id-4 not found."),
    ],
)
async def test_authorized_user_invalid_record_cancel(
    authorized_client_for_scheduling: AsyncClient,
    record_id: str,
    expected_status: int,
    expected_detail: str,
):
    # Send request to cancel the record
    res = await authorized_client_for_scheduling.delete(f"/bookings/cancel/{record_id}")

    # Assert the expected status code
    assert res.status_code == expected_status

    # Assert the error detail message
    assert res.json().get("detail") == expected_detail


# ============================================================================
# Unauthorized user cancels valid/invalid booking
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "record_id",
    [
        # See data.sql for the available slots
        "b6732344-bc30-4401-9a69-b91e28273b8d",  # valid slot ID
        "25db80a6-68ab-43c2-8dc2-6bee617b7827",  # invalid slot ID
    ],
)
async def test_unauthorized_user_cancel(async_client: AsyncClient, record_id: str):

    json_body = {"booking_slot_id": record_id}
    res: Response = await async_client.post("/bookings/schedule", json=json_body)

    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


# ============================================================================
# Authorized user reschedules valid booking
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "record_id, new_slot_id",
    [
        # See data.sql for the available records
        (
            "a6578d08-4e81-40ca-bc30-c9f2d01024aa",
            "e7bbc307-ae75-4854-bd91-d6851ae085fd",
        ),
    ],
)
async def test_authorized_user_valid_reschedule(
    authorized_client_for_scheduling: AsyncClient, record_id: str, new_slot_id: str
):
    json_body = {"vaccine_record_id": record_id, "new_slot_id": new_slot_id}
    res: Response = await authorized_client_for_scheduling.post(
        "/bookings/reschedule", json=json_body
    )

    assert res.status_code == 200

    rescheduled_slot = VaccineRecordResponse(**res.json())

    assert str(rescheduled_slot.id) == record_id
    assert str(rescheduled_slot.booking_slot_id) == new_slot_id
    assert rescheduled_slot.status.value == "booked"
    assert (
        str(rescheduled_slot.user_id)
        == authorized_client_for_scheduling.headers["user_id"]
    )


# ============================================================================
# Authorized user reschedules invalid booking (reschedule slot or new slot invalid)
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "record_id, new_slot_id, expected_status, expected_error_message",
    [
        (
            "b6732344-bc30-4401-9a69-b91e28273b8d",  # invalid record as it belongs to another user
            "213fa5e7-abbb-4e55-bccc-318db42ace81",  # valid slot as it is available
            401,
            "You are not authorized to cancel this vaccination slot.",
        ),
        (
            "a6578d08-4e81-40ca-bc30-c9f2d01024aa",  # valid slot as it belongs to user
            "97ba51db-48d8-4873-b1ee-57a9b7f766f0",  # invalid slot as it belongs to another user
            400,
            "Slot already booked",
        ),
        (
            "a6578d08-4e81-40ca-bc30-c9f2d01024aa",  # valid slot as it belongs to user
            "00000000-0000-0000-0000-000000000000",  # invalid as it does not exist
            404,
            "Booking slot with ID 00000000-0000-0000-0000-000000000000 not found.",
        ),
        # Invalid record id (doesn't exist)
        (
            "00000000-0000-0000-0000-000000000000",  # invalid as it does not exist
            "213fa5e7-abbb-4e55-bccc-318db42ace81",  # valid slot as it is available
            404,  # Not found
            "Vaccine record with id 00000000-0000-0000-0000-000000000000 not found.",
        ),
    ],
)
async def test_authorized_user_invalid_reschedule(
    authorized_client_for_scheduling: AsyncClient,
    record_id: str,
    new_slot_id: str,
    expected_status: int,
    expected_error_message: str,
):
    json_body = {"vaccine_record_id": record_id, "new_slot_id": new_slot_id}

    res: Response = await authorized_client_for_scheduling.post(
        "/bookings/reschedule", json=json_body
    )

    # Assert status code
    assert res.status_code == expected_status

    # Assert error message
    response_data = res.json()
    assert "detail" in response_data
    assert expected_error_message in response_data["detail"]


# ============================================================================
# Unauthorized user reschedules
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "record_id, new_slot_id",
    [
        # See data.sql for the available records
        (
            "b6732344-bc30-4401-9a69-b91e28273b8d",
            "213fa5e7-abbb-4e55-bccc-318db42ace81",
        ),
    ],
)
async def test_unauthorized_user_reschedule(
    async_client: AsyncClient, record_id: str, new_slot_id: str
):
    json_body = {"vaccine_record_id": record_id, "new_slot_id": new_slot_id}
    res: Response = await async_client.post("/bookings/reschedule", json=json_body)

    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"
