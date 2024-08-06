from pytest import fixture, mark
from httpx import AsyncClient, ASGITransport

from shopen.main import app


@fixture(scope='session')
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@mark.anyio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200