"""Tests for CSV filename validation and path resolution."""

import pytest

from web_interface import is_safe_csv_filename, resolve_csv_path


@pytest.mark.parametrize('name,ok', [
    ('instagram_profiles_20260101.csv', True),
    ('export-v2.csv', True),
    ('../etc/passwd.csv', False),
    ('..\\windows.csv', False),
    ('sub/dir.csv', False),
    ('file.txt', False),
    ('', False),
    ('a b.csv', False),
])
def test_is_safe_csv_filename(name, ok):
    assert is_safe_csv_filename(name) is ok


def test_resolve_csv_path_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / 'scraped_data'
    d.mkdir()
    good = d / 'safe.csv'
    good.write_text('a,b\n1,2\n')

    assert resolve_csv_path('safe.csv') == good.resolve()
    assert resolve_csv_path('../../../etc/passwd.csv') is None
    missing = resolve_csv_path('nope.csv')
    assert missing is not None
    assert not missing.is_file()
