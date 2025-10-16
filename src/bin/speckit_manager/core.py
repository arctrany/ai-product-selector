"""
Core Spec Kit Manager Module

Wraps GitHub Spec Kit CLI functionality with additional features.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging

from .installer import SpecKitInstaller
from .config import ConfigManager
from .project_detector import ProjectTypeDetector

logger = logging.getLogger(__name__)


class SpecKitManager:
    """Main wrapper for GitHub Spec Kit CLI with enhanced functionality."""
    
    def __init__(self, project_root: Optional[str] = None, auto_install: bool = True):
        """
        Initialize Spec Kit Manager.
        
        Args:
            project_root: Project root directory (current dir if None)
            auto_install: Automatically install Spec Kit if not found
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.installer = SpecKitInstaller()
        self.config = ConfigManager(self.project_root)
        
        # Ensure Spec Kit is installed
        if auto_install and not self.installer.is_installed():
            logger.info("Spec Kit not found, installing...")
            if not self.installer.install():
                raise RuntimeError("Failed to install Spec Kit")
    
    def is_speckit_project(self) -> bool:
        """Check if current directory is a Spec Kit project."""
        return (self.project_root / ".specify").exists()
    
    def init_project(self, 
                    project_name: Optional[str] = None,
                    project_type: Optional[str] = None,
                    force: bool = False) -> bool:
        """
        Initialize a new Spec Kit project.
        
        Args:
            project_name: Name of the project (directory name if None)
            project_type: Type of project (auto-detected if None)
            force: Force initialization even if already initialized

        Returns:
            True if successful, False otherwise
        """
        if self.is_speckit_project() and not force:
            logger.warning("Project already initialized. Use force=True to reinitialize.")
            return True

        if not project_name:
            project_name = self.project_root.name

        # Auto-detect project type if not specified
        if not project_type:
            detector = ProjectTypeDetector(self.project_root)
            detected_type, confidence = detector.detect_project_type()

            if confidence > 0.5:
                project_type = detected_type
                logger.info(f"Auto-detected project type: {project_type} (confidence: {confidence:.2f})")
            else:
                project_type = "java-spring-boot"  # fallback default
                logger.warning(f"Could not reliably detect project type (confidence: {confidence:.2f}), using default: {project_type}")
            
        try:
            # Run spec-kit init command
            result = self._run_speckit_command([
                "init",
                "--name", project_name,
                "--type", project_type
            ])
            
            if result.returncode == 0:
                # Update our configuration
                self.config.update_project_config({
                    "name": project_name,
                    "type": project_type,
                    "initialized": True
                })
                
                logger.info(f"Successfully initialized Spec Kit project: {project_name}")
                return True
            else:
                logger.error(f"Spec Kit init failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize project: {e}")
            return False
    
    def constitution(self, create: bool = False, update: bool = False) -> Optional[str]:
        """
        Manage project constitution.
        
        Args:
            create: Create a new constitution
            update: Update existing constitution
            
        Returns:
            Constitution content if successful, None otherwise
        """
        try:
            cmd = ["constitution"]
            if create:
                cmd.append("--create")
            if update:
                cmd.append("--update")
                
            result = self._run_speckit_command(cmd)
            
            if result.returncode == 0:
                # Read constitution file
                constitution_file = self.project_root / ".specify" / "memory" / "constitution.md"
                if constitution_file.exists():
                    return constitution_file.read_text()
                return result.stdout
            else:
                logger.error(f"Constitution command failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to manage constitution: {e}")
            return None
    
    def specify(self, feature_name: str, description: Optional[str] = None) -> bool:
        """
        Create a feature specification.
        
        Args:
            feature_name: Name of the feature
            description: Optional feature description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = ["specify", feature_name]
            if description:
                cmd.extend(["--description", description])
                
            result = self._run_speckit_command(cmd)
            
            if result.returncode == 0:
                logger.info(f"Successfully created specification for: {feature_name}")
                return True
            else:
                logger.error(f"Specify command failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create specification: {e}")
            return False
    
    def plan(self, feature_name: str) -> bool:
        """
        Create implementation plan for a feature.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._run_speckit_command(["plan", feature_name])
            
            if result.returncode == 0:
                logger.info(f"Successfully created plan for: {feature_name}")
                return True
            else:
                logger.error(f"Plan command failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            return False
    
    def tasks(self, feature_name: str) -> bool:
        """
        Generate tasks for a feature.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._run_speckit_command(["tasks", feature_name])
            
            if result.returncode == 0:
                logger.info(f"Successfully generated tasks for: {feature_name}")
                return True
            else:
                logger.error(f"Tasks command failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to generate tasks: {e}")
            return False
    
    def implement(self, feature_name: str) -> bool:
        """
        Execute implementation for a feature.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._run_speckit_command(["implement", feature_name])
            
            if result.returncode == 0:
                logger.info(f"Successfully implemented: {feature_name}")
                return True
            else:
                logger.error(f"Implement command failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to implement feature: {e}")
            return False
    
    def full_workflow(self, feature_name: str, description: Optional[str] = None) -> bool:
        """
        Execute the full Spec Kit workflow for a feature.
        
        Args:
            feature_name: Name of the feature
            description: Optional feature description
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting full workflow for feature: {feature_name}")
        
        # Ensure constitution exists
        if not (self.project_root / ".specify" / "memory" / "constitution.md").exists():
            logger.info("Creating project constitution...")
            if not self.constitution(create=True):
                logger.error("Failed to create constitution")
                return False
        
        # Execute workflow steps
        steps = [
            ("specify", lambda: self.specify(feature_name, description)),
            ("plan", lambda: self.plan(feature_name)),
            ("tasks", lambda: self.tasks(feature_name)),
            ("implement", lambda: self.implement(feature_name))
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Executing step: {step_name}")
            if not step_func():
                logger.error(f"Workflow failed at step: {step_name}")
                return False
        
        logger.info(f"Full workflow completed successfully for: {feature_name}")
        return True
    
    def list_features(self) -> List[str]:
        """List all features in the project."""
        specs_dir = self.project_root / "specs"
        if not specs_dir.exists():
            return []
            
        features = []
        for item in specs_dir.iterdir():
            if item.is_dir():
                features.append(item.name)
        
        return sorted(features)
    
    def get_feature_status(self, feature_name: str) -> Dict[str, Any]:
        """Get status information for a specific feature."""
        feature_dir = self.project_root / "specs" / feature_name
        if not feature_dir.exists():
            return {"exists": False}
            
        status = {"exists": True}
        
        # Check for various files
        files_to_check = ["spec.md", "plan.md", "tasks.md"]
        for file_name in files_to_check:
            file_path = feature_dir / file_name
            status[file_name.replace(".md", "")] = file_path.exists()
            
        return status
    
    def _run_speckit_command(self, args: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """
        Run a Spec Kit CLI command.
        
        Args:
            args: Command arguments
            cwd: Working directory (project root if None)
            
        Returns:
            Completed process result
        """
        if not self.installer.is_installed():
            raise RuntimeError("Spec Kit is not installed")
            
        cmd = [str(self.installer.speckit_executable)] + args
        work_dir = cwd or str(self.project_root)
        
        logger.debug(f"Running command: {' '.join(cmd)} in {work_dir}")
        
        return subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get comprehensive project information."""
        return {
            "project_root": str(self.project_root),
            "is_speckit_project": self.is_speckit_project(),
            "speckit_installed": self.installer.is_installed(),
            "speckit_version": self.installer.get_installed_version(),
            "features": self.list_features(),
            "config": self.config.get_all_config()
        }