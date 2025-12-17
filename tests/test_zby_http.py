import types
import pytest
import requests
from types import SimpleNamespace

from sources.zby_http import search_via_api


class DummyResp:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload

    def json(self):
        return self._payload


def test_search_via_api_success(monkeypatch):
    sample = {"code":1, "data": {"rows": [{"standardNum":"GB/T 123","standardName":"测试","hasPdf":1}]}}

    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResp(200, sample)

    sess = requests.Session()
    monkeypatch.setattr(sess, 'post', fake_post)
    rows = search_via_api('测试', page=1, page_size=10, session=sess)
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]['standardName'] == '测试'


def test_search_via_api_failure(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResp(500, {})

    sess = requests.Session()
    monkeypatch.setattr(sess, 'post', fake_post)
    rows = search_via_api('nope', session=sess)
    assert rows == []
