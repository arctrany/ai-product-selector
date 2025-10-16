"""
Spec-Kit Manager - A Python wrapper for GitHub Spec Kit

This package provides a modular Python interface to GitHub Spec Kit,
with additional features for Deep Wiki integration and Aone Copilot support.
"""

__version__ = "0.1.0"
__author__ = "Aone Copilot Team"

from .core import SpecKitManager
from .installer import SpecKitInstaller
from .deep_wiki import DeepWikiManager
from .config import ConfigManager

__all__ = [
    'SpecKitManager',
    'SpecKitInstaller', 
    'DeepWikiManager',
    'ConfigManager'
]