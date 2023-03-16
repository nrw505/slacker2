import pytest

from slacker.webapp.routes import index


def test_home_content():
    result = index()
    assert result == "SLAAAAACK"
