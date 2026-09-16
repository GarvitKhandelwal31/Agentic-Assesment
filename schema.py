"""Pydantic schema for a single app research record."""
from typing import Literal
from pydantic import BaseModel, Field


class AppRecord(BaseModel):
    id: int
    name: str
    category: str
    one_liner: str = Field(description="What the app does in one sentence")
    auth_methods: list[str] = Field(description="e.g. ['OAuth2', 'API Key']")
    self_serve: Literal["yes", "partial", "gated", "unknown"] = Field(
        description="Can a dev get free/trial credentials without sales contact?"
    )
    self_serve_notes: str = Field(description="Specific plan/gate details")
    api_type: str = Field(description="REST, GraphQL, REST+GraphQL, SDK-only, CLI-only, No-API")
    api_breadth: Literal["narrow", "moderate", "broad", "unknown"]
    mcp_exists: bool = Field(description="Is there an official or well-known MCP server?")
    mcp_notes: str = Field(default="", description="MCP server details or link")
    buildability: Literal["ready", "needs-outreach", "gated", "no-api"]
    main_blocker: str = Field(description="Primary reason it cannot be built today, or 'none'")
    evidence_url: str = Field(description="Primary docs URL that supports these answers")
    agent_confidence: float = Field(ge=0.0, le=1.0, description="Agent self-assessed confidence 0-1")
    verified: bool = Field(default=False)
    verification_notes: str = Field(default="")
