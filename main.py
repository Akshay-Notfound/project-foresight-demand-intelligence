"""
main.py — Root ASGI entrypoint alias for Render / Cloud hosting.
Exposes the FastAPI scoring service app from service.main.
"""
from service.main import app

__all__ = ["app"]
