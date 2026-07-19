"""Research source connectors (local-first, optional network)."""
from connectors.registry import get_connector, list_connectors
__all__ = ["get_connector", "list_connectors"]
