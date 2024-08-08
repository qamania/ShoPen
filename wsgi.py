from a2wsgi import ASGIMiddleware
from shopen.main import app as ASGI_APP

WSGI_APP = ASGIMiddleware(ASGI_APP)
