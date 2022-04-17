import pytest
from lib.ArDa.arda_db import ArDa_DB, ArDa_DB_Bib, ArDa_DB_Obsid, ArDa_DB_SQL
from os.path import exists
from os import remove

@pytest.fixture(name="db_sql")
def make_arda_db_sql():
    return ArDa_DB_SQL()

@pytest.fixture(name="db_obsid")
def make_arda_db_obsid():
    return ArDa_DB_Obsid()

@pytest.fixture(name="db_bib")
def make_arda_db_bib():
    return ArDa_DB_Bib()

@pytest.mark.parametrize("arda_db, db_type",
                            [("db_sql", "sqllite"),
                             ("db_obsid", "obsidian"),
                             ("db_bib", "bibtex")])
def test_make_arda(arda_db, db_type, request):
    # Tests whether db type is properly set for each arda type
    arda_db = request.getfixturevalue(arda_db) # This is needed to use fixtures in parametrizations
    assert arda_db.db_type == db_type

@pytest.mark.parametrize("arda_db", [("db_sql"), ("db_obsid"), ("db_bib")])
def test_make_new_arda_db(arda_db, request):
    # Tests whether we can successfully create a new db skeleton
    arda_db = request.getfixturevalue(arda_db) # This is needed to use fixtures in parametrizations

    if arda_db.db_type == "sqllite":
        file_path = "tests/test_dbs/test_temp_db.sqlite"
        arda_db.make_new_db(file_path)

        assert exists(file_path)
        # Clean up for testing next time
        remove(file_path)
        assert not exists(file_path)
    elif arda_db.db_type == "obsidian":
        file_path = "tests/test_dbs/test_temp_obsid2"
        arda_db.make_new_db(file_path)
        assert exists(file_path)
    elif arda_db.db_type == "bibtex":
        file_path = "tests/test_dbs/test_temp_bib"
        arda_db.make_new_db(file_path)
        assert exists(file_path)
    else:
        raise NotImplementedError

    assert arda_db.db_path == file_path

@pytest.mark.parametrize("arda_db, file_path", [("db_sql", "tests/test_dbs/test_db.sqlite"),
                                                 ("db_obsid", "tests/test_dbs/test_db_obsid"), 
                                                 ("db_bib", "tests/test_dbs/test_db_bib")])
def test_open_arda_db(arda_db, file_path, request):
    # Tests whether we can successfully open an existing db
    arda_db = request.getfixturevalue(arda_db) # This is needed to use fixtures in parametrizations

    arda_db.open_db(file_path)
    assert arda_db.db_path == file_path