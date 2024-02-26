"""Test for docq.manage_organisations module."""
import logging as log
import os
import sqlite3
import tempfile
from contextlib import closing, suppress
from typing import Generator, Optional
from unittest.mock import patch

import pytest
from docq.constants import DEFAULT_ORG_ID

TEST_USER_ID = 1005

@pytest.fixture(scope="session")
def manage_orgs_test_dir() -> Generator:
    """Return the sqlite system file."""
    from docq.manage_organisations import _init

    log.info("Setup manage organisations tests...")

    with tempfile.TemporaryDirectory() as temp_dir, patch(
        "docq.manage_organisations.get_sqlite_shared_system_file"
    ) as get_sqlite_shared_system_file:
        sqlite_system_file = os.path.join(temp_dir, "system.db")
        get_sqlite_shared_system_file.return_value = sqlite_system_file
        _init()

        yield (
            temp_dir,
            sqlite_system_file,
            get_sqlite_shared_system_file,
        )

    log.info("Teardown manage organisations tests...")


def insert_test_org(sqlite_system_file: str, name: str) -> Optional[int]:
    """Insert test org."""
    with closing(sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO orgs (name) VALUES (?)",
            (name,),
        )
        org_id = cursor.lastrowid
        connection.commit()
        return org_id


def test_db_init(manage_orgs_test_dir: tuple) -> None:
    """Test database init."""
    sqlite_system_file = manage_orgs_test_dir[1]
    with closing(sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(connection.cursor()) as cursor:
        sql_select = "SELECT name FROM sqlite_master WHERE type='table' AND name = ?"
        cursor.execute(sql_select, ("orgs",))

        assert cursor.fetchone() is not None, "Table orgs should exist"


@pytest.mark.first()
def test_init_default_org_if_necessary() -> None:
    """Test init_default_org_if_necessary."""
    from docq.manage_organisations import _init_default_org_if_necessary

    with patch("docq.manage_organisations.manage_settings._init_default_system_settings"
        ) as _init_default_system_settings, patch("docq.manage_organisations.manage_settings._init_default_org_settings"
        ) as _init_default_org_settings:
        assert _init_default_org_if_necessary() is True, "Default org should be created"

        _init_default_system_settings.assert_called_once()
        _init_default_org_settings.assert_called_once_with(DEFAULT_ORG_ID)

        assert _init_default_org_if_necessary() is False, "Default org should not be created"


def test_list_organisations(manage_orgs_test_dir: tuple) -> None:
    """Test list_organisations."""
    from docq.manage_organisations import list_organisations
    from docq.manage_users import _init

    sqlite_system_file = manage_orgs_test_dir[1]
    with patch("docq.manage_users.get_sqlite_shared_system_file") as get_sqlite_shared_system_file:
        get_sqlite_shared_system_file.return_value = sqlite_system_file
        _init()

    org_names = ["Test_list_organisations_org_1", "Test_list_organisations_org_2"]
    org_id = insert_test_org(sqlite_system_file, org_names[0])

    assert org_id is not None, "The sample list organisations test org should not be None"
    org_list = list_organisations(name_match=org_names[0])

    assert org_list is not None, "The sample list organisations test org should not be None"
    assert len(org_list) == 1, "Expected only one org to be returned."
    assert org_list[0][0] == org_id, "The sample list organisations test org id should match"

    org_id = insert_test_org(sqlite_system_file, org_names[1])
    with closing(sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("INSERT INTO users (username, password, fullname) VALUES (?, ?, ?)", ("list_orgs_test_user", "test_password", "Test User"))
        user_id = cursor.lastrowid

        assert user_id is not None, "The sample list organisations test user should not be None"
        cursor.execute(
            "INSERT INTO org_members (user_id, org_id) VALUES (?, ?)",
            (user_id, org_id),
        )
        connection.commit()

    org_list = list_organisations(user_id=user_id)
    assert org_list is not None, "The sample list organisations test org should not be None"
    assert len(org_list) == 1, "Expected only one org to be returned."
    assert org_list[0][0] == org_id, "The sample list organisations test org id should match"


def test_create_organisation_sql(manage_orgs_test_dir: tuple) -> None:
    """Test _create_organisation_sql."""
    from docq.manage_organisations import _create_organisation_sql

    org_name = "Test_create_organisation_sql_org"
    sqlite_system_file = manage_orgs_test_dir[1]
    with closing(sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(connection.cursor()) as cursor:
        cursor = _create_organisation_sql(cursor, org_name)
        connection.commit()

        cursor.execute("SELECT name FROM orgs WHERE name = ?", (org_name,))
        assert cursor.fetchone() is not None, "The sample create organisation test org should exist"


def test_create_organisation(manage_orgs_test_dir: tuple) -> None:
    """Test create_organisation."""
    from docq.manage_organisations import create_organisation

    org_name = "Test_create_organisation_org"
    sqlite_system_file = manage_orgs_test_dir[1]

    with patch("docq.manage_organisations.manage_users._add_organisation_member_sql"
        ) as _add_organisation_member_sql, patch("docq.manage_organisations.manage_settings._init_default_org_settings"
        ) as _init_default_org_settings:
        org_id = create_organisation(org_name, TEST_USER_ID)

        assert org_id is not None, "The sample create organisation test org should not be None"
        _add_organisation_member_sql.assert_called_once()
        _init_default_org_settings.assert_called_once_with(org_id)

        with suppress(Exception):
            duplicate = create_organisation(org_name, TEST_USER_ID)
            assert duplicate is None, "Creating org with duplicate name should fail."

    with closing(sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT name FROM orgs WHERE name = ?", (org_name,))
        assert cursor.fetchone() is not None, "The sample create organisation test org should exist"


def test_update_organisation(manage_orgs_test_dir: tuple) -> None:
    """Test update_organisation."""
    from docq.manage_organisations import update_organisation

    org_name = "Test_update_organisation_org"
    org_name_updated = "Test_update_organisation_org_updated"
    sqlite_system_file = manage_orgs_test_dir[1]
    org_id = insert_test_org(sqlite_system_file, org_name)
    ctrl_org_name = "Test_update_organisation_ctrl_org"
    ctrl_org_id = insert_test_org(sqlite_system_file, ctrl_org_name)

    assert org_id is not None, "The sample update organisation test org should not be None"
    assert ctrl_org_id is not None, "The sample update organisation control org should not be None"
    assert update_organisation(org_id, org_name_updated ) is True, "The sample update organisation test org should be updated"

    with suppress(Exception):
        assert update_organisation(org_id, ctrl_org_name) is False, "Updating org with duplicate name should fail."

    with closing(sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT name FROM orgs WHERE name = ?", (org_name_updated,))
        assert cursor.fetchone() is not None, "The updated org should exist"

        cursor.execute("SELECT id, name FROM orgs WHERE name = ?", (ctrl_org_name,))
        org = cursor.fetchone()
        assert org is not None, "The control org should exist"
        assert org[0] == ctrl_org_id, "The control org id should match"


def test_archive_organisation(manage_orgs_test_dir: tuple) -> None:
    """Test archive_organisation."""
    from docq.manage_organisations import archive_organisation

    org_name = "Test_archive_organisation_org"
    sqlite_system_file = manage_orgs_test_dir[1]
    org_id = insert_test_org(sqlite_system_file, org_name)

    assert org_id is not None, "The sample archive organisation test org should not be None"
    assert archive_organisation(org_id) is True, "The sample archive organisation test org should be archived"

    with closing(sqlite3.connect(sqlite_system_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT name, archived FROM orgs WHERE name = ?", (org_name,))
        org = cursor.fetchone()

    assert org is not None, "The archived org should not exist"
    assert org[0] == org_name, "The archived org name should match"
    assert org[1] == 1, "The archived org should be archived"



