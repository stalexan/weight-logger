#!/usr/bin/env python3

""" Test weight-log-service """

# Standard library imports
import datetime

# 3rd party imports
from http import HTTPStatus
from fastapi import HTTPException
import pytest

# Local imports
from service import Service
from service.entry import WeightLogEntry
from service.token import Token
from service.user import User

# Service
service: Service = Service()

# User
USERNAME: str = "Betty"
PASSWORD: str = "boop de doop"
USER_ID: int = 100

def test_create_user():
    """ Test creating a user. """

    # Create user.
    goal_weight: float = 68
    metric: bool = False
    service.user_manager.add_user(USERNAME, metric, goal_weight, PASSWORD)

    # Verify user was created.
    users: list[User] = service.user_manager.get_users()
    assert len(users) == 1
    user: User = users[0]
    assert user.id == USER_ID
    assert user.username == USERNAME
    assert user.metric == metric
    assert user.units_name == "lb"
    assert user.goal_weight == goal_weight

def test_login():
    """ Test login. """

    token: Token = service.login(USERNAME, PASSWORD)
    user: User = service.get_user_from_token(token.token)
    assert user.username == USERNAME

def create_entries(
    entries_data: list[tuple[int, datetime.date, float, bool]]) -> list[WeightLogEntry]:
    """ Create WeightLogEntry instances from entries_data. """

    return [
        WeightLogEntry(id = entry_data[0], user_id = USER_ID, date = entry_data[1],
            weight = entry_data[2], is_metric= entry_data[3])
        for entry_data in entries_data]

def check_entries(left: list[WeightLogEntry], right: list[WeightLogEntry]) -> None:
    """ Check that entries are equal. """

    for left_entry, right_entry in zip(left, right):
        assert left_entry == right_entry

def test_add_entries():
    """ Test adding weight log entries. """

    # Create entries to add.
    entries_to_add: list[WeightLogEntry] = create_entries([
        (0, datetime.date(2022, 3, 22), 123.5, False),
        (0, datetime.date(2022, 3, 23), 124.0, False),
        (0, datetime.date(2022, 3, 26), 126.0, False),
        (0, datetime.date(2022, 3, 24), 125.0, False),
        (0, datetime.date(2022, 3, 27), 127.0, False)])

    # Add entries.
    for entry in entries_to_add:
        service.add_entry(entry)

    # Are entries the same?
    entries_to_add.sort(key=lambda entry: entry.date)
    user: User = service.user_manager.get_user_from_id(USER_ID)
    check_entries(service.get_entries(user), entries_to_add)

def test_add_entry_fail():
    """ Test that adding an entry with a duplicate date fails. """

    entry: WeightLogEntry = WeightLogEntry(
        user_id = USER_ID,
        date = datetime.date(2022, 3, 24),
        weight = 120,
        is_metric= False)
    with pytest.raises(HTTPException) as exc_info:
        service.add_entry(entry)
        assert exc_info.value is HTTPException
        http_ex: HTTPException = exc_info.value
        assert http_ex.status == HTTPStatus.BAD_REQUEST

def test_update_entry():
    """ Test updating an entry. """

    # Update entry.
    entry: WeightLogEntry = WeightLogEntry(
        id = 102,
        user_id = USER_ID,
        date = datetime.date(2022, 3, 26),
        weight = 119,
        is_metric= False)
    service.update_entry(entry)

    # Was entry updated?
    updated_entry: WeightLogEntry = service.get_entry_from_entry_id(entry.id)
    assert updated_entry == entry

def test_update_fails():
    """ Test updating a non-existent entry fails. """

    entry: WeightLogEntry = WeightLogEntry(
        id = 109,
        user_id = USER_ID,
        date = datetime.date(2022, 3, 26),
        weight = 119,
        is_metric= False)
    with pytest.raises(HTTPException) as exc_info:
        service.update_entry(entry)
        assert exc_info.value is HTTPException
        http_ex: HTTPException = exc_info.value
        assert http_ex.status == HTTPStatus.BAD_REQUEST

def test_delete_entry():
    """ Test deleting an entry. """

    # Confirm entry exists.
    date: datetime.date = datetime.date(2022, 3, 23)
    entry: WeightLogEntry = service.get_entry_from_user_id(USER_ID, date)

    # Delete entry.
    service.delete_entry(USER_ID, date)

    # Confirm entry no longer exists.
    assert service.get_entry_from_entry_id(entry.id) is None

def test_delete_entry_fails():
    """ Test delete failure for non-existent date. """

    with pytest.raises(HTTPException) as exc_info:
        service.delete_entry(USER_ID, datetime.date(2022, 2, 23))
        assert exc_info.value is HTTPException
        http_ex: HTTPException = exc_info.value
        assert http_ex.status == HTTPStatus.BAD_REQUEST

def test_get_entries():
    """ Test get of all entries for current user. """

    # Create expected entries.
    expected_entries: list[WeightLogEntry] = create_entries([
        (100, datetime.date(2022, 3, 22), 123.5, False),
        (103, datetime.date(2022, 3, 24), 125.0, False),
        (102, datetime.date(2022, 3, 26), 119.0, False),
        (104, datetime.date(2022, 3, 27), 127.0, False)])

    # Get and check entries.
    user: User = service.user_manager.get_user_from_id(USER_ID)
    check_entries(service.get_entries(user), expected_entries)
