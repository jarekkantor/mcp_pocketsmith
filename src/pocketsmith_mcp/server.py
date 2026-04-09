"""FastMCP server creation and configuration for PocketSmith."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.config import get_config
from pocketsmith_mcp.logger import get_logger
from pocketsmith_mcp.tools import register_all_tools
from pocketsmith_mcp.user_context import UserContext

logger = get_logger("server")


async def _resolve_user_id(client: PocketSmithClient) -> int:
    """Fetch the authenticated user's ID from /me."""
    me = await client.get("/me")
    if not isinstance(me, dict) or "id" not in me:
        raise ValueError("Unexpected response from /me endpoint")
    user_id = int(me["id"])
    logger.info(f"Resolved user_id={user_id} (login={me.get('login', 'unknown')})")
    return user_id


def create_server(api_key: str | None = None) -> FastMCP:
    """
    Create and configure the PocketSmith MCP server.

    The user ID is automatically resolved from the API key on startup
    via the server lifespan, so no tool calls require a user_id parameter.

    Args:
        api_key: Optional API key override. If not provided,
                 loads from POCKETSMITH_API_KEY environment variable.

    Returns:
        Configured FastMCP server instance with all tools registered.

    Raises:
        ValueError: If no API key is provided or found in environment.
    """
    config = get_config()

    key = api_key or config.api_key
    if not key:
        raise ValueError(
            "POCKETSMITH_API_KEY environment variable required. "
            "Set it in your environment or .env file."
        )

    logger.info("Creating PocketSmith MCP server")

    client = PocketSmithClient(
        api_key=key,
        timeout=config.api_timeout,
        max_retries=config.max_retries,
        rate_limit_per_minute=config.rate_limit_per_minute,
    )

    user_ctx = UserContext()

    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[None]:
        """Resolve user_id before serving requests (once per process; HTTP may re-enter lifespan)."""
        if not user_ctx.is_resolved:
            user_ctx.user_id = await _resolve_user_id(client)
        yield

    # Env FASTMCP_HOST/FASTMCP_PORT are not applied unless passed into FastMCP().
    http_host = os.getenv("FASTMCP_HOST", "127.0.0.1")
    http_port = int(os.getenv("FASTMCP_PORT", "8000"))

    mcp = FastMCP(
        "pocketsmith-mcp",
        lifespan=lifespan,
        host=http_host,
        port=http_port,
    )

    register_all_tools(mcp, client, user_ctx)

    logger.info("PocketSmith MCP server created successfully")

    return mcp


def get_server() -> FastMCP:
    """
    Get or create the PocketSmith MCP server singleton.

    This is the main entry point for running the server.

    Returns:
        Configured FastMCP server instance.
    """
    return create_server()
