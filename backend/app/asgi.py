import atexit
from contextlib import asynccontextmanager
from functools import partial

from a2wsgi import WSGIMiddleware
from anyio import to_thread
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.cors import CORSMiddleware

from app import create_app
from app.mcp_tools import create_mcp_server


def create_asgi_app(flask_app=None):
    """One process and one set of business services for both HTTP surfaces."""
    if flask_app is None:
        flask_app = create_app()
    mcp = create_mcp_server(
        flask_app.config["STORAGE"],
        flask_app.config["APP_CONFIG"],
        flask_app.extensions["testcase_job_manager"],
        flask_app.extensions["coverage_job_manager"],
    )
    app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        ),
    )
    # Keep the SDK's exact /mcp route ahead of the Flask fallback.
    wsgi = WSGIMiddleware(flask_app)
    app.mount("/", wsgi)
    sdk_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(app):
        try:
            async with sdk_lifespan(app):
                yield
        finally:
            for name in ("system_task_manager", "testcase_job_manager", "coverage_job_manager"):
                manager = flask_app.extensions[name]
                await to_thread.run_sync(partial(manager.shutdown, wait=True))
                atexit.unregister(manager.shutdown)
            await to_thread.run_sync(partial(wsgi.executor.shutdown, wait=True))

    app.router.lifespan_context = lifespan
    # Accept all hosts and origins, matching the existing REST access policy.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS", "PUT", "PATCH"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id", "MCP-Protocol-Version"],
    )
    app.state.flask_app = flask_app
    app.state.mcp = mcp
    return app
