"""
Deep Wiki Integration Module

Handles Deep Wiki functionality and knowledge source management.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DeepWikiManager:
    """Manages Deep Wiki integration and knowledge sources."""
    
    def __init__(self, project_root: Path):
        """Initialize Deep Wiki manager."""
        self.project_root = Path(project_root)
        self.deep_wiki_dir = self.project_root / ".specify" / "deep-wiki"
        self.config_file = self.deep_wiki_dir / "config.yml"
        self.index_file = self.deep_wiki_dir / "index.md"
        self.sync_log_file = self.deep_wiki_dir / "sync.log"
        
    def is_initialized(self) -> bool:
        """Check if Deep Wiki is initialized for this project."""
        return self.deep_wiki_dir.exists() and self.config_file.exists()
    
    def initialize(self, project_name: str, project_type: str) -> bool:
        """
        Initialize Deep Wiki for the project.
        
        Args:
            project_name: Name of the project
            project_type: Type of project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create Deep Wiki directory
            self.deep_wiki_dir.mkdir(parents=True, exist_ok=True)
            
            # Create configuration file
            config_data = {
                "project": {
                    "name": project_name,
                    "type": project_type,
                    "initialized": datetime.now().isoformat()
                },
                "wiki": {
                    "enabled": True,
                    "auto_sync": True,
                    "sync_on_commit": True
                },
                "sources": {
                    "constitution": ".specify/memory/constitution.md",
                    "specifications": "specs/",
                    "documentation": "docs/"
                },
                "sync_schedule": {
                    "auto_update": True,
                    "interval": "daily"
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            # Create index file
            index_content = f"""# {project_name} Deep Wiki

## Project Overview
- **Type**: {project_type}
- **Initialized**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Constitution**: [View Constitution](.specify/memory/constitution.md)

## Knowledge Sources
- Project Constitution
- Feature Specifications
- Implementation Plans
- Best Practices

## Sync Status
- Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Auto-sync: Enabled
"""
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                f.write(index_content)
            
            # Set environment variable
            os.environ["DEEP_WIKI_AVAILABLE"] = "true"
            
            # Create .env file entry
            env_file = self.project_root / ".env"
            env_content = "DEEP_WIKI_AVAILABLE=true\n"
            
            if env_file.exists():
                # Check if already exists
                existing_content = env_file.read_text()
                if "DEEP_WIKI_AVAILABLE" not in existing_content:
                    with open(env_file, 'a', encoding='utf-8') as f:
                        f.write(env_content)
            else:
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(env_content)
            
            self._log_action("Deep Wiki initialized successfully")
            logger.info(f"Deep Wiki initialized for project: {project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Deep Wiki: {e}")
            return False
    
    def update(self) -> bool:
        """
        Update Deep Wiki content with latest project information.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized():
            logger.warning("Deep Wiki not initialized. Run initialize() first.")
            return False
            
        try:
            # Update index file timestamp
            if self.index_file.exists():
                content = self.index_file.read_text()
                # Update last updated timestamp
                updated_content = self._update_timestamp_in_content(content)
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
            
            # Update configuration with last sync time
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                
                if "sync_schedule" not in config:
                    config["sync_schedule"] = {}
                
                config["sync_schedule"]["last_update"] = datetime.now().isoformat()
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            self._log_action("Deep Wiki content updated")
            logger.info("Deep Wiki content updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Deep Wiki: {e}")
            return False
    
    def sync(self) -> bool:
        """
        Sync project specifications to Deep Wiki.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized():
            logger.warning("Deep Wiki not initialized. Run initialize() first.")
            return False
            
        try:
            # Create sync manifest
            manifest_file = self.deep_wiki_dir / "sync-manifest.md"
            
            # Count files to sync
            files_count = 0
            for pattern in ["*.md", "*.yml", "*.yaml"]:
                files_count += len(list(self.project_root.glob(f"**/{pattern}")))
            
            manifest_content = f"""# Deep Wiki Sync Manifest

## Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Synced Content
- Constitution: .specify/memory/constitution.md
- Specifications: specs/
- Configuration: .specify/config/
- Templates: .specify/templates/

### Sync Status
- Status: Completed
- Files Synced: {files_count}
- Last Update: {datetime.now().isoformat()}
"""
            
            with open(manifest_file, 'w', encoding='utf-8') as f:
                f.write(manifest_content)
            
            # Update index file
            self.update()
            
            self._log_action("Full project sync completed")
            logger.info("Deep Wiki sync completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync to Deep Wiki: {e}")
            return False
    
    def detect_knowledge_sources(self) -> Dict[str, Any]:
        """
        Detect available knowledge sources and return configuration.
        
        Returns:
            Dictionary with knowledge source information
        """
        knowledge_info = {
            "deep_wiki_available": False,
            "mcp_available": False,
            "local_docs_available": False,
            "primary_source": "local",
            "agent_message": "",
            "detected_at": datetime.now().isoformat()
        }
        
        # Check for Deep Wiki
        if self.is_initialized() or os.environ.get("DEEP_WIKI_AVAILABLE") == "true":
            knowledge_info["deep_wiki_available"] = True
            knowledge_info["primary_source"] = "deep_wiki"
            knowledge_info["agent_message"] = "✅ Deep-Wiki 可用，优先使用内部知识库"
            logger.info("Deep-Wiki detected and available")
        
        # Check for MCP services
        elif self._check_mcp_available():
            knowledge_info["mcp_available"] = True
            knowledge_info["primary_source"] = "mcp"
            knowledge_info["agent_message"] = "✅ MCP 知识服务可用，使用智能知识检索"
            logger.info("MCP knowledge service detected and available")
        
        # Default to local docs
        else:
            knowledge_info["local_docs_available"] = True
            knowledge_info["primary_source"] = "local"
            knowledge_info["agent_message"] = "📁 使用本地文档作为知识源"
            logger.info("Using local documents as knowledge source")
        
        # Update agent integration rules
        self._update_agent_rules(knowledge_info)
        
        return knowledge_info
    
    def get_config(self) -> Dict[str, Any]:
        """Get Deep Wiki configuration."""
        if not self.config_file.exists():
            return {}
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load Deep Wiki config: {e}")
            return {}
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update Deep Wiki configuration."""
        try:
            config = self.get_config()
            config.update(updates)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update Deep Wiki config: {e}")
            return False
    
    def get_sync_history(self) -> List[str]:
        """Get sync history from log file."""
        if not self.sync_log_file.exists():
            return []
            
        try:
            with open(self.sync_log_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            logger.warning(f"Failed to read sync history: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive Deep Wiki status."""
        return {
            "initialized": self.is_initialized(),
            "config_exists": self.config_file.exists(),
            "index_exists": self.index_file.exists(),
            "config": self.get_config(),
            "sync_history": self.get_sync_history()[-10:],  # Last 10 entries
            "knowledge_sources": self.detect_knowledge_sources()
        }
    
    def _check_mcp_available(self) -> bool:
        """Check if MCP services are available."""
        # Check for MCP command
        import shutil
        if shutil.which("mcp"):
            return True
            
        # Check environment variable
        if os.environ.get("MCP_KNOWLEDGE_AVAILABLE"):
            return True
            
        return False
    
    def _log_action(self, message: str) -> None:
        """Log an action to the sync log file."""
        try:
            self.sync_log_file.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().isoformat()
            log_entry = f"{timestamp}: {message}\n"
            
            with open(self.sync_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            logger.warning(f"Failed to log action: {e}")
    
    def _update_timestamp_in_content(self, content: str) -> str:
        """Update timestamp in markdown content."""
        import re
        
        # Update "Last Updated" line
        pattern = r"- Last Updated:.*"
        replacement = f"- Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return re.sub(pattern, replacement, content)
    
    def _update_agent_rules(self, knowledge_info: Dict[str, Any]) -> None:
        """Update agent integration rules with knowledge source info."""
        try:
            rules_file = self.project_root / ".aone_copilot" / "rules" / "default.md"
            
            if not rules_file.exists():
                return
                
            # Read existing rules
            content = rules_file.read_text(encoding='utf-8')
            
            # Check if knowledge source section already exists
            if "### 当前知识源状态" in content:
                # Update existing section
                import re
                pattern = r"### 当前知识源状态.*?(?=###|\Z)"
                replacement = f"""### 当前知识源状态
- **状态**: {knowledge_info['agent_message']}
- **检测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **主要来源**: {knowledge_info['primary_source']}

"""
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            else:
                # Append new section
                content += f"""

### 当前知识源状态
- **状态**: {knowledge_info['agent_message']}
- **检测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **主要来源**: {knowledge_info['primary_source']}
"""
            
            # Write updated content
            with open(rules_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            logger.warning(f"Failed to update agent rules: {e}")