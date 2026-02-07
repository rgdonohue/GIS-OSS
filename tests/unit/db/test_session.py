from src.api.config import Settings
from src.db.session import resolve_read_dsn


def test_resolve_read_dsn_prefers_readonly_dsn():
    settings = Settings(
        environment="test",
        db_read_dsn="postgresql://ro:secret@localhost:5432/gis_oss",
        db_dsn="postgresql://rw:secret@localhost:5432/gis_oss",
    )

    assert resolve_read_dsn(settings) == "postgresql://ro:secret@localhost:5432/gis_oss"


def test_resolve_read_dsn_falls_back_to_primary_dsn():
    settings = Settings(
        environment="test",
        db_read_dsn="",
        db_dsn="postgresql://rw:secret@localhost:5432/gis_oss",
    )

    assert resolve_read_dsn(settings) == "postgresql://rw:secret@localhost:5432/gis_oss"


def test_resolve_read_dsn_builds_conninfo_from_read_role():
    settings = Settings(
        environment="test",
        db_name="gis_oss",
        db_host="db",
        db_port=5432,
        db_user="gis_user",
        db_password="rw_pw",
        db_read_user="gis_readonly",
        db_read_password="ro_pw",
    )

    assert resolve_read_dsn(settings) == (
        "dbname=gis_oss user=gis_readonly password=ro_pw host=db port=5432"
    )


def test_resolve_read_dsn_falls_back_to_legacy_credentials():
    settings = Settings(
        environment="test",
        db_name="gis_oss",
        db_host="db",
        db_port=5432,
        db_user="gis_user",
        db_password="rw_pw",
        db_read_user="",
        db_read_password="",
    )

    assert resolve_read_dsn(settings) == (
        "dbname=gis_oss user=gis_user password=rw_pw host=db port=5432"
    )


def test_resolve_read_dsn_legacy_fallback_with_read_defaults_unset():
    settings = Settings(
        environment="test",
        db_name="gis_oss",
        db_host="db",
        db_port=5432,
        db_user="gis_user",
        db_password="rw_pw",
    )

    assert resolve_read_dsn(settings) == (
        "dbname=gis_oss user=gis_user password=rw_pw host=db port=5432"
    )
