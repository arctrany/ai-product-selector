"""
GitHub Spec Kit Installer Module

Handles installation and management of GitHub Spec Kit CLI.
"""

import os
import sys
import subprocess
import shutil
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SpecKitInstaller:
    """Manages GitHub Spec Kit installation and updates."""
    
    def __init__(self, install_dir: Optional[str] = None):
        """Initialize installer with optional custom install directory."""
        self.install_dir = Path(install_dir) if install_dir else Path.home() / ".speckit"
        self.bin_dir = self.install_dir / "bin"
        self.speckit_executable = self.bin_dir / "speckit"
        
    def is_installed(self) -> bool:
        """Check if Spec Kit is already installed."""
        return self.speckit_executable.exists() and self.speckit_executable.is_file()
    
    def get_installed_version(self) -> Optional[str]:
        """Get the currently installed Spec Kit version."""
        if not self.is_installed():
            return None
            
        try:
            result = subprocess.run(
                [str(self.speckit_executable), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Extract version from output like "speckit v0.0.64"
                version_line = result.stdout.strip()
                if "v" in version_line:
                    return version_line.split("v")[-1].strip()
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.warning(f"Failed to get Spec Kit version: {e}")
            return None
    
    def get_latest_version(self) -> Optional[str]:
        """Get the latest available Spec Kit version from GitHub."""
        try:
            response = requests.get(
                "https://api.github.com/repos/github/spec-kit/releases/latest",
                timeout=10
            )
            if response.status_code == 200:
                release_data = response.json()
                tag_name = release_data.get("tag_name", "")
                # Remove 'v' prefix if present
                return tag_name.lstrip("v")
            return None
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch latest Spec Kit version: {e}")
            return None
    
    def install(self, version: Optional[str] = None, force: bool = False) -> bool:
        """
        Install GitHub Spec Kit CLI.
        
        Args:
            version: Specific version to install (latest if None)
            force: Force reinstallation even if already installed
            
        Returns:
            True if installation successful, False otherwise
        """
        if self.is_installed() and not force:
            logger.info("Spec Kit is already installed. Use force=True to reinstall.")
            return True
            
        # Get version to install
        target_version = version or self.get_latest_version()
        if not target_version:
            logger.error("Could not determine Spec Kit version to install")
            return False
            
        logger.info(f"Installing Spec Kit v{target_version}...")
        
        # Create installation directory
        self.install_dir.mkdir(parents=True, exist_ok=True)
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine platform and architecture
        platform = self._get_platform()
        arch = self._get_architecture()
        
        if not platform or not arch:
            logger.error("Unsupported platform or architecture")
            return False
            
        # Download and install
        download_url = f"https://github.com/github/spec-kit/releases/download/v{target_version}/speckit-{platform}-{arch}"
        
        try:
            # Download the binary
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()
            
            # Write to executable file
            with open(self.speckit_executable, "wb") as f:
                f.write(response.content)
                
            # Make executable
            os.chmod(self.speckit_executable, 0o755)
            
            # Verify installation
            if self.verify_installation():
                logger.info(f"Successfully installed Spec Kit v{target_version}")
                self._add_to_path()
                return True
            else:
                logger.error("Installation verification failed")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Failed to download Spec Kit: {e}")
            return False
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify that Spec Kit is properly installed and working."""
        if not self.is_installed():
            return False
            
        try:
            result = subprocess.run(
                [str(self.speckit_executable), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def update(self) -> bool:
        """Update Spec Kit to the latest version."""
        current_version = self.get_installed_version()
        latest_version = self.get_latest_version()
        
        if not latest_version:
            logger.error("Could not determine latest version")
            return False
            
        if current_version == latest_version:
            logger.info(f"Spec Kit is already up to date (v{current_version})")
            return True
            
        logger.info(f"Updating Spec Kit from v{current_version} to v{latest_version}")
        return self.install(version=latest_version, force=True)
    
    def uninstall(self) -> bool:
        """Uninstall Spec Kit."""
        try:
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
                logger.info("Spec Kit uninstalled successfully")
                return True
            else:
                logger.info("Spec Kit is not installed")
                return True
        except Exception as e:
            logger.error(f"Failed to uninstall Spec Kit: {e}")
            return False
    
    def _get_platform(self) -> Optional[str]:
        """Get the current platform name for downloads."""
        system = sys.platform.lower()
        if system.startswith("linux"):
            return "linux"
        elif system.startswith("darwin"):
            return "darwin"
        elif system.startswith("win"):
            return "windows"
        return None
    
    def _get_architecture(self) -> Optional[str]:
        """Get the current architecture for downloads."""
        import platform
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64"]:
            return "amd64"
        elif arch in ["arm64", "aarch64"]:
            return "arm64"
        elif arch in ["i386", "i686", "x86"]:
            return "386"
        return None
    
    def _add_to_path(self) -> None:
        """Add Spec Kit bin directory to PATH if not already present."""
        bin_path = str(self.bin_dir)
        current_path = os.environ.get("PATH", "")
        
        if bin_path not in current_path.split(os.pathsep):
            # Add to current session
            os.environ["PATH"] = f"{bin_path}{os.pathsep}{current_path}"
            
            # Suggest adding to shell profile
            logger.info(f"Add this to your shell profile to make speckit available globally:")
            logger.info(f'export PATH="{bin_path}:$PATH"')
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information about Spec Kit installation."""
        return {
            "installed": self.is_installed(),
            "install_dir": str(self.install_dir),
            "executable_path": str(self.speckit_executable),
            "current_version": self.get_installed_version(),
            "latest_version": self.get_latest_version(),
            "verified": self.verify_installation() if self.is_installed() else False
        }