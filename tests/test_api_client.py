import pytest

from rubberneck.services.api_client import (
    DnDAPI,
    ResourceNotFound,
)


class FakeResponse:
    def __init__(self, status, payload=None, text=""):
        self.status = status
        self.payload = payload
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def json(self):
        return self.payload

    async def text(self):
        return self._text


class FakeSession:
    def __init__(self, response, calls, **kwargs):
        self.response = response
        self.calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    def get(self, url, **kwargs):
        self.calls.append(url)
        return self.response


class TestDnDAPI:
    @pytest.mark.asyncio
    async def test_lists_resources_and_caches_response(self):
        calls = []
        response = FakeResponse(
            200,
            {
                "results": [
                    {
                        "index": "cover",
                        "name": "Cover",
                        "url": "/api/2014/rule-sections/cover",
                    }
                ]
            },
        )
        client = DnDAPI(
            session_factory=lambda **kwargs: FakeSession(response, calls, **kwargs)
        )

        first = await client.list_resources("rule-sections")
        second = await client.list_resources("rule-sections")

        assert first[0].index == "cover"
        assert second == first
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_normalises_friendly_rule_name(self):
        calls = []
        response = FakeResponse(
            200,
            {"index": "making-an-attack", "name": "Making an Attack", "desc": "Text"},
        )
        client = DnDAPI(
            session_factory=lambda **kwargs: FakeSession(response, calls, **kwargs)
        )

        await client.get_resource("rule-sections", " Making an Attack ")

        assert calls[0].endswith("/rule-sections/making-an-attack")

    @pytest.mark.asyncio
    async def test_raises_specific_error_for_missing_rule(self):
        client = DnDAPI(
            session_factory=lambda **kwargs: FakeSession(
                FakeResponse(404), [], **kwargs
            )
        )

        with pytest.raises(ResourceNotFound):
            await client.get_resource("rule-sections", "not-real")
