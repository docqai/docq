"""Tests for docq.manage_users module."""

import logging as log
import os
import sqlite3
import tempfile
from contextlib import closing, suppress
from typing import Generator, Optional
from unittest.mock import patch

import pytest
from argon2.exceptions import VerificationError


@pytest.fixture(scope="session")
def manage_users_test_dir() -> Generator:
    """Return the sqlite system file."""
    from docq.manage_users import _init

    log.info("Setup manage users tests...")

    with tempfile.TemporaryDirectory() as temp_dir, patch(
        "docq.manage_users.get_sqlite_system_file"
    ) as get_sqlite_system_file:
        sqlite_system_file = os.path.join(temp_dir, "system.db")
        get_sqlite_system_file.return_value = sqlite_system_file
        _init()

        yield temp_dir, sqlite_system_file, get_sqlite_system_file,

    log.info("Teardown manage users tests...")


def insert_test_user(sqlite_system_file: str, username: str) -> Optional[int]:
    """Insert test user."""
    from docq.manage_users import PH

    with closing(
        sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO users (username, password, fullname) VALUES (?, ?, ?)",
            (username, PH.hash("password"), username,),
        )
        user_id = cursor.lastrowid
        connection.commit()
        return user_id


def test_db_init(manage_users_test_dir: tuple) -> None:
    """Test database init."""
    sqlite_system_file = manage_users_test_dir[1]
    with closing(
        sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        sql_select = "SELECT name FROM sqlite_master WHERE type='table' AND name = ?"
        tables = [("users",), ("org_members",)]

        for table in tables:
            cursor.execute(sql_select, table)
            assert cursor.fetchone() is not None, f"Table {table[0]} should exist"


@pytest.mark.first()
def test_init_admin_if_necessary() -> None:
    """Test init_admin_if_necessary."""
    from docq.manage_users import _init_admin_if_necessary

    with patch("docq.manage_users.add_organisation_member") as add_organisation_member:
        assert _init_admin_if_necessary(), "The default admin user should be created"

        add_organisation_member.assert_called_once()
        assert _init_admin_if_necessary() is False, "The default admin user should not be created again"


def test_init_user_data(manage_users_test_dir: tuple) -> None:
    """Test _init_user_data."""
    from docq.manage_users import _init_user_data

    sqlite_system_file = manage_users_test_dir[1]
    with patch("docq.manage_users.msettings._init") as msettings_init:
        user_id = insert_test_user(sqlite_system_file, "test_init_user_data")
        assert user_id is not None, "User should be created"
        _init_user_data(user_id)

        msettings_init.assert_called_once_with(user_id)


def test_authenticate(manage_users_test_dir: tuple) -> None:
    """Test authenticate."""
    from docq.manage_users import authenticate, set_user_as_verified

    sqlite_system_file = manage_users_test_dir[1]

    user_id = insert_test_user(sqlite_system_file, "test_authenticate")
    ctrl_user_id = insert_test_user(sqlite_system_file, "test_authenticate_ctrl")

    assert user_id is not None, "User should be created"
    assert ctrl_user_id is not None, "User should be created"

    set_user_as_verified(user_id)
    with patch("docq.manage_users.msettings._init") as msettings_init:
        msettings_init.return_value = None
        auth_results =  authenticate("test_authenticate", "password")
        assert auth_results is not None, "User should be authenticated"
        assert auth_results[0] == user_id, "User id should match"

        with suppress(VerificationError):
            assert authenticate("test_authenticate", "wrong_password") is None, "Wrong password should not authenticate"

        assert authenticate("test_authenticate_ctrl", "password") is None, "Unverified user should not authenticate"


def test_get_user(manage_users_test_dir: tuple) -> None:
    """Test get_user."""
    from docq.manage_users import get_user

    sqlite_system_file = manage_users_test_dir[1]

    user_id = insert_test_user(sqlite_system_file, "test_get_user")

    assert user_id is not None, "Test get user should be created"

    for user in [get_user(user_id=user_id), get_user(username="test_get_user")]:
        assert user is not None, "Test get user should be returned"
        assert user[0] == user_id, "User id should match"

    with suppress(ValueError):
        assert get_user() is None, "No user should be returned"


def test_list_users(manage_users_test_dir: tuple) -> None:
    """Test list_users."""
    from docq.manage_users import list_users

    sqlite_system_file = manage_users_test_dir[1]

    user_id = insert_test_user(sqlite_system_file, "test_list_users_test")

    assert user_id is not None, "Test list users should be created"

    user_list = list_users()
    assert user_list is not None, "Test list users should be returned"
    assert len(user_list) >= 1, "Atleast one user should be returned."

    user_list = list_users(username_match="test_list_users_test")
    assert user_list is not None, "Test list users should be returned"
    assert len(user_list) == 1, "Expected only one user to be returned."
    assert user_list[0][0] == user_id, "User id should match"


def test_list_users_by_org(manage_users_test_dir: tuple) -> None:
    """Test list_users_by_org."""
    from docq.manage_organisations import _init
    from docq.manage_users import list_users_by_org

    sqlite_system_file = manage_users_test_dir[1]
    user_id = insert_test_user(sqlite_system_file, "test_list_users_by_org_test")
    ctrl_user_id = insert_test_user(sqlite_system_file, "test_list_users_by_org_ctrl_test")

    assert user_id is not None, "Test list users by org should be created"
    assert ctrl_user_id is not None, "Test list users by org should be created"

    with patch("docq.manage_organisations.get_sqlite_system_file") as get_sqlite_system_file:
        get_sqlite_system_file.return_value = sqlite_system_file
        _init()

    with closing(
        sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?", ("orgs",)
        )
        org = cursor.fetchone()

        assert org is not None, "Org table should exist"

        cursor.execute(
            "INSERT INTO orgs (name) VALUES (?)",
            ("test_list_users_by_org_test",),
        )
        org_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO orgs (name) VALUES (?)",
            ("test_list_users_by_org_ctrl_test",),
        )
        ctrl_org_id = cursor.lastrowid

        assert org_id is not None, "Test list users by org should be created"
        assert ctrl_org_id is not None, "Test list users by org should be created"

        cursor.execute(
            "INSERT INTO org_members (user_id, org_id) VALUES (?, ?)",
            (user_id, org_id,),
        )
        cursor.execute(
            "INSERT INTO org_members (user_id, org_id, org_admin) VALUES (?, ?, ?)",
            (ctrl_user_id, org_id, 1),
        )
        connection.commit()

    user_list = list_users_by_org(org_id=org_id)

    assert user_list is not None, "Test list users by org should be returned"
    assert len(user_list) == 2, "Expected only two users to be returned."

    user_list = list_users_by_org(org_id=org_id, username_match="test_list_users_by_org_test")

    assert user_list is not None, "Test list users by org should be returned"
    assert len(user_list) == 1, "Expected only one user to be returned."

    user_list = list_users_by_org(org_id=org_id, org_admin_match=True)

    assert user_list is not None, "Test list users by org should be returned"
    assert len(user_list) == 1, "Expected only one user to be returned."

    user_list = list_users_by_org(org_id=org_id, org_admin_match=False)

    assert user_list is not None, "Test list users by org should be returned"
    assert len(user_list) == 1, "Expected only one user to be returned."


def test_list_selected_users(manage_users_test_dir: tuple) -> None:
    """Test list selected users."""
    from docq.manage_users import list_selected_users

    sqlite_system_file = manage_users_test_dir[1]
    user_id1 = insert_test_user(sqlite_system_file, "test_list_selected_users1")
    user_id2 = insert_test_user(sqlite_system_file, "test_list_selected_users2")
    ctrl_user_id = insert_test_user(sqlite_system_file, "test_list_selected_users_ctrl")

    assert user_id1 is not None, "Test list selected users should be created"
    assert user_id2 is not None, "Test list selected users should be created"
    assert ctrl_user_id is not None, "Test list selected users should be created"

    user_list = list_selected_users([user_id1, user_id2])

    assert user_list is not None, "Test list selected users should be returned"
    assert len(user_list) == 2, "Expected only two users to be returned."
    assert user_id1 in [x[0] for x in user_list], "User id should match"
    assert user_id2 in [x[0] for x in user_list], "User id should match"
    assert ctrl_user_id not in [x[0] for x in user_list], "User id should not match"


def test_update_user(manage_users_test_dir: tuple) -> None:
    """Test update user."""
    from docq.manage_users import update_user

    sqlite_system_file = manage_users_test_dir[1]
    user_id = insert_test_user(sqlite_system_file, "test_update_user")
    ctrl_user_id = insert_test_user(sqlite_system_file, "test_update_user_ctrl")
    update_username = "test_update_user_updated"

    assert user_id is not None, "Test update user should be created"
    assert ctrl_user_id is not None, "Test update user should be created"

    update_user(user_id, username=update_username)

    with closing(
        sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT username FROM users WHERE id = ?", (user_id,)
        )
        updated_user = cursor.fetchone()

        assert updated_user is not None, "Test update user should be returned"
        assert updated_user[0] == update_username, "Username should be updated"
