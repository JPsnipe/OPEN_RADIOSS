from pathlib import Path
import sys
from starlite import Starlite, get
from starlite.response import Response

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cdb2rad.parser import parse_cdb
from src.dashboard.app import viewer_html

@get('/viewer')
def viewer(file: str) -> Response:
    nodes, elements, *_ = parse_cdb(file)
    html = viewer_html(nodes, elements)
    return Response(html, media_type='text/html')

app = Starlite(route_handlers=[viewer])

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
