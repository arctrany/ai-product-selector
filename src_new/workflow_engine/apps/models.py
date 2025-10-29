"""Application configuration models."""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


@dataclass
class FlowConfig:
    """Configuration for a single flow within an app."""
    entry_point: str
    metadata_function: Optional[str] = None
    description: Optional[str] = None
    version: str = "1.0.0"
    enabled: bool = True

    # Flow metadata
    flow_id: Optional[str] = None
    title: Optional[str] = None


@dataclass
class AppConfig:
    """Application configuration model."""
    app_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # UI configuration
    console_title: Optional[str] = None
    console_subtitle: Optional[str] = None

    # Flow configuration
    _flow_ids: Optional[List[str]] = field(default=None, init=False)  # Internal field
    default_flow_id: str = "default"
    extensions: Optional[List[str]] = None

    # Legacy support
    entry_point: Optional[str] = None

    # New flow-based configuration
    flows: Optional[Dict[str, FlowConfig]] = None

    def __post_init__(self):
        """Post-initialization processing."""
        if self.flows is None:
            self.flows = {}

        # Handle flow_ids from JSON input (if present)
        if hasattr(self, '_temp_flow_ids'):
            self._flow_ids = getattr(self, '_temp_flow_ids')
            delattr(self, '_temp_flow_ids')

        # Convert dict flows to FlowConfig objects if needed
        if self.flows and isinstance(list(self.flows.values())[0], dict):
            converted_flows = {}
            for flow_id, flow_data in self.flows.items():
                if isinstance(flow_data, dict):
                    converted_flows[flow_id] = FlowConfig(**flow_data)
                else:
                    converted_flows[flow_id] = flow_data
            self.flows = converted_flows

    @property
    def flow_ids(self) -> List[str]:
        """Get list of flow IDs."""
        # First check if we have explicit flow_ids from JSON
        if self._flow_ids is not None:
            return self._flow_ids
        # Then check flows configuration
        if self.flows:
            return list(self.flows.keys())
        # Fallback to default
        return [self.default_flow_id] if self.entry_point else []


@dataclass
class AppRunContext:
    """Runtime context for app execution."""
    app_id: str
    flow_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)