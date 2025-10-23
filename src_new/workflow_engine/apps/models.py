"""Application configuration models."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AppExtension(BaseModel):
    """Application extension configuration."""
    
    type: str = Field(..., description="Extension type (e.g., 'browser_preview', 'custom_widget')")
    title: str = Field(..., description="Extension display title")
    enabled: bool = Field(default=True, description="Whether extension is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="Extension-specific configuration")


class FlowConfig(BaseModel):
    """Flow configuration within an application."""

    flow_id: str = Field(..., description="Unique flow identifier")
    version: str = Field(default="1.0.0", description="Flow version")
    title: str = Field(..., description="Flow display title (Chinese name)")
    description: Optional[str] = Field(None, description="Flow description")
    entry_point: str = Field(..., description="Flow entry point module:function")
    metadata_function: Optional[str] = Field(None, description="Flow metadata function module:function")

class AppConfig(BaseModel):
    """Application configuration model."""

    app_id: str = Field(..., description="Unique application identifier")
    name: str = Field(..., alias="app_name", description="Application display name")
    description: Optional[str] = Field(None, description="Application description")
    version: str = Field(default="1.0.0", description="Application version")

    # Console configuration
    console_title: str = Field(..., description="Console page title")
    console_subtitle: Optional[str] = Field(None, description="Console page subtitle")

    # Flow associations
    flow_ids: List[str] = Field(default_factory=list, description="Associated workflow IDs")
    default_flow_id: Optional[str] = Field(None, description="Default workflow ID")

    # Flow configurations (new multi-flow support)
    flows: Optional[Dict[str, FlowConfig]] = Field(None, description="Flow configurations")

    # Legacy entry point (for backward compatibility)
    entry_point: Optional[str] = Field(None, description="Legacy single flow entry point")
    
    # Extensions
    extensions: List[AppExtension] = Field(default_factory=list, description="Application extensions")
    
    # Metadata
    author: Optional[str] = Field(None, description="Application author")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    def get_flow_id(self, flow_name: Optional[str] = None) -> Optional[str]:
        """Get flow ID by name or return default."""
        if flow_name and flow_name in self.flow_ids:
            return flow_name
        return self.default_flow_id or (self.flow_ids[0] if self.flow_ids else None)
    
    def has_extension(self, extension_type: str) -> bool:
        """Check if application has specific extension type."""
        return any(ext.type == extension_type and ext.enabled for ext in self.extensions)
    
    def get_extension(self, extension_type: str) -> Optional[AppExtension]:
        """Get extension configuration by type."""
        for ext in self.extensions:
            if ext.type == extension_type and ext.enabled:
                return ext
        return None


class AppRunContext(BaseModel):
    """Application run context for console view."""
    
    app_config: AppConfig
    flow_id: str
    run_id: Optional[str] = None
    thread_id: Optional[str] = None
    
    @property
    def console_id(self) -> str:
        """Generate console ID from app_id and flow_id."""
        return f"{self.app_config.app_id}-{self.flow_id}"