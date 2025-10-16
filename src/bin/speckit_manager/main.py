#!/usr/bin/env python3
"""
Spec-Kit Manager Main Entry Point

A Python wrapper for GitHub Spec Kit with enhanced functionality.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from .core import SpecKitManager
from .installer import SpecKitInstaller
from .deep_wiki import DeepWikiManager
from .config import ConfigManager
from .project_detector import ProjectTypeDetector


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def cmd_install(args) -> int:
    """Install or update GitHub Spec Kit."""
    installer = SpecKitInstaller()
    
    if args.check:
        status = installer.get_status()
        print(f"Installed: {status['installed']}")
        print(f"Version: {status['current_version'] or 'Not installed'}")
        print(f"Latest: {status['latest_version'] or 'Unknown'}")
        return 0
    
    if args.uninstall:
        if installer.uninstall():
            print("Spec Kit uninstalled successfully")
            return 0
        else:
            print("Failed to uninstall Spec Kit")
            return 1
    
    if args.update:
        if installer.update():
            print("Spec Kit updated successfully")
            return 0
        else:
            print("Failed to update Spec Kit")
            return 1
    
    # Default: install
    if installer.install(version=args.version, force=args.force):
        print("Spec Kit installed successfully")
        return 0
    else:
        print("Failed to install Spec Kit")
        return 1


def cmd_init(args) -> int:
    """Initialize a new Spec Kit project."""
    try:
        manager = SpecKitManager(args.directory, auto_install=True)
        
        # Auto-detect project type if not specified
        project_type = args.type
        if not project_type:
            detector = ProjectTypeDetector(Path(args.directory or '.'))
            detected_type, confidence = detector.detect_project_type()

            if confidence > 0.5:
                project_type = detected_type
                print(f"Auto-detected project type: {project_type} (confidence: {confidence:.2f})")
            else:
                project_type = "java-spring-boot"  # fallback default
                print(f"Could not reliably detect project type (confidence: {confidence:.2f}), using default: {project_type}")

        if manager.init_project(
            project_name=args.name,
            project_type=project_type,
            force=args.force
        ):
            print(f"Project '{args.name or Path(args.directory or '.').name}' initialized successfully")
            
            # Initialize Deep Wiki if requested
            if args.deep_wiki:
                deep_wiki = DeepWikiManager(Path(args.directory or '.'))
                if deep_wiki.initialize(
                    args.name or Path(args.directory or '.').name,
                    project_type
                ):
                    print("Deep Wiki initialized successfully")
                else:
                    print("Warning: Failed to initialize Deep Wiki")
            
            return 0
        else:
            print("Failed to initialize project")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_constitution(args) -> int:
    """Manage project constitution."""
    try:
        manager = SpecKitManager(args.directory)
        
        result = manager.constitution(create=args.create, update=args.update)
        
        if result:
            if args.show:
                print(result)
            else:
                print("Constitution managed successfully")
            return 0
        else:
            print("Failed to manage constitution")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_workflow(args) -> int:
    """Execute Spec Kit workflow commands."""
    try:
        manager = SpecKitManager(args.directory)
        
        if args.command == "specify":
            success = manager.specify(args.feature, args.description)
        elif args.command == "plan":
            success = manager.plan(args.feature)
        elif args.command == "tasks":
            success = manager.tasks(args.feature)
        elif args.command == "implement":
            success = manager.implement(args.feature)
        elif args.command == "full":
            success = manager.full_workflow(args.feature, args.description)
        else:
            print(f"Unknown workflow command: {args.command}")
            return 1
        
        if success:
            print(f"Workflow '{args.command}' completed successfully")
            return 0
        else:
            print(f"Workflow '{args.command}' failed")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_deep_wiki(args) -> int:
    """Manage Deep Wiki functionality."""
    try:
        project_root = Path(args.directory or '.')
        deep_wiki = DeepWikiManager(project_root)
        
        if args.action == "init":
            project_name = args.name or project_root.name

            # Auto-detect project type if not specified
            project_type = args.type
            if not project_type:
                detector = ProjectTypeDetector(project_root)
                detected_type, confidence = detector.detect_project_type()

                if confidence > 0.5:
                    project_type = detected_type
                    print(f"Auto-detected project type: {project_type} (confidence: {confidence:.2f})")
                else:
                    project_type = "java-spring-boot"  # fallback default
                    print(f"Could not reliably detect project type (confidence: {confidence:.2f}), using default: {project_type}")

            if deep_wiki.initialize(project_name, project_type):
                print("Deep Wiki initialized successfully")
                return 0
            else:
                print("Failed to initialize Deep Wiki")
                return 1
                
        elif args.action == "update":
            if deep_wiki.update():
                print("Deep Wiki updated successfully")
                return 0
            else:
                print("Failed to update Deep Wiki")
                return 1
                
        elif args.action == "sync":
            if deep_wiki.sync():
                print("Deep Wiki sync completed successfully")
                return 0
            else:
                print("Failed to sync Deep Wiki")
                return 1
                
        elif args.action == "status":
            status = deep_wiki.get_status()
            print(f"Initialized: {status['initialized']}")
            print(f"Config exists: {status['config_exists']}")
            print(f"Index exists: {status['index_exists']}")
            if status['sync_history']:
                print("Recent sync history:")
                for entry in status['sync_history']:
                    print(f"  {entry}")
            return 0
            
        elif args.action == "detect":
            sources = deep_wiki.detect_knowledge_sources()
            print(f"Primary source: {sources['primary_source']}")
            print(f"Deep Wiki available: {sources['deep_wiki_available']}")
            print(f"MCP available: {sources['mcp_available']}")
            print(f"Message: {sources['agent_message']}")
            return 0
            
        else:
            print(f"Unknown Deep Wiki action: {args.action}")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_status(args) -> int:
    """Show project status."""
    try:
        manager = SpecKitManager(args.directory)
        info = manager.get_project_info()
        
        print(f"Project Root: {info['project_root']}")
        print(f"Is Spec Kit Project: {info['is_speckit_project']}")
        print(f"Spec Kit Installed: {info['speckit_installed']}")
        print(f"Spec Kit Version: {info['speckit_version'] or 'Unknown'}")
        print(f"Features: {len(info['features'])}")
        
        if info['features']:
            print("Available features:")
            for feature in info['features']:
                status = manager.get_feature_status(feature)
                status_str = []
                if status.get('spec'): status_str.append('spec')
                if status.get('plan'): status_str.append('plan')
                if status.get('tasks'): status_str.append('tasks')
                print(f"  {feature}: {', '.join(status_str) if status_str else 'empty'}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Spec-Kit Manager - Python wrapper for GitHub Spec Kit",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '-d', '--directory',
        help='Project directory (default: current directory)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install or manage Spec Kit')
    install_parser.add_argument('--version', help='Specific version to install')
    install_parser.add_argument('--force', action='store_true', help='Force reinstallation')
    install_parser.add_argument('--update', action='store_true', help='Update to latest version')
    install_parser.add_argument('--uninstall', action='store_true', help='Uninstall Spec Kit')
    install_parser.add_argument('--check', action='store_true', help='Check installation status')
    install_parser.set_defaults(func=cmd_install)
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize new Spec Kit project')
    init_parser.add_argument('--name', help='Project name')
    init_parser.add_argument('--type', help='Project type (auto-detected if not specified)')
    init_parser.add_argument('--force', action='store_true', help='Force initialization')
    init_parser.add_argument('--deep-wiki', action='store_true', help='Initialize Deep Wiki')
    init_parser.set_defaults(func=cmd_init)
    
    # Constitution command
    const_parser = subparsers.add_parser('constitution', help='Manage project constitution')
    const_parser.add_argument('--create', action='store_true', help='Create new constitution')
    const_parser.add_argument('--update', action='store_true', help='Update existing constitution')
    const_parser.add_argument('--show', action='store_true', help='Show constitution content')
    const_parser.set_defaults(func=cmd_constitution)
    
    # Workflow commands
    workflow_parser = subparsers.add_parser('workflow', help='Execute workflow commands')
    workflow_parser.add_argument('command', choices=['specify', 'plan', 'tasks', 'implement', 'full'])
    workflow_parser.add_argument('feature', help='Feature name')
    workflow_parser.add_argument('--description', help='Feature description')
    workflow_parser.set_defaults(func=cmd_workflow)
    
    # Deep Wiki commands
    wiki_parser = subparsers.add_parser('deep-wiki', help='Manage Deep Wiki')
    wiki_parser.add_argument('action', choices=['init', 'update', 'sync', 'status', 'detect'])
    wiki_parser.add_argument('--name', help='Project name (for init)')
    wiki_parser.add_argument('--type', help='Project type (for init)')
    wiki_parser.set_defaults(func=cmd_deep_wiki)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show project status')
    status_parser.set_defaults(func=cmd_status)
    
    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())