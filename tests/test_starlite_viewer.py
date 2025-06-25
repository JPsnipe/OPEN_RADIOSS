import os
import asyncio
from httpx import AsyncClient, ASGITransport
from scripts.starlite_viewer import app

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')

def test_starlite_viewer_route():
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get('/viewer', params={'file': DATA})
            assert resp.status_code == 200
            assert 'OrbitControls' in resp.text

    asyncio.run(_run())
