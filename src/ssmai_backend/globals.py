"""
Global objects for SSMai Backend
"""

from typing import Optional
from ssmai_backend.mcp.client import MCPClient

class MCPContainer:
    client: Optional[MCPClient] = None

# Global MCP container instance
mcp_container = MCPContainer()
