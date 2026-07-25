"""Reusable API, catalog, search, and navigation services."""

from .api_client import DnDAPI, DnDAPIError, ResourceNotFound, ResourceReference
from .reference_catalog import (
    CONDITION,
    REFERENCE_TYPES,
    RULE,
    AutocompleteMetrics,
    ReferenceCatalog,
    ReferenceEntry,
    ReferenceType,
)
from .reference_relations import ReferenceRelations
from .reference_search import InvalidSearchQuery, ReferenceSearchIndex, SearchResult

__all__ = [
    "CONDITION",
    "REFERENCE_TYPES",
    "RULE",
    "AutocompleteMetrics",
    "DnDAPI",
    "DnDAPIError",
    "InvalidSearchQuery",
    "ReferenceCatalog",
    "ReferenceEntry",
    "ReferenceRelations",
    "ReferenceSearchIndex",
    "ReferenceType",
    "ResourceNotFound",
    "ResourceReference",
    "SearchResult",
]
