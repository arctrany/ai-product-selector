#!/usr/bin/env python3
"""
Advanced Chrome process analyzer with detailed process type identification
and user data directory analysis.
"""

import os
import sys
import subprocess
import re
import json
import platform
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


class ChromeProcessAnalyzer:
    """Advanced Chrome process analyzer."""
    
    def __init__(self):
        self.system = platform.system().lower()
        
    def analyze_processes(self) -> Dict:
        """
        Analyze all Chrome/Chromium processes on the system.
        
        Returns:
            Dictionary containing detailed process analysis
        """
        analysis = {
            'system': self.system,
            'processes': [],
            'main_processes': [],
            'child_processes': defaultdict(list),
            'user_data_dirs': set(),
            'profiles': set()
        }
        
        if self.system == "darwin":  # macOS
            processes = self._analyze_macos_processes()
        elif self.system == "windows":
            processes = self._analyze_windows_processes()
        elif self.system == "linux":
            processes = self._analyze_linux_processes()
        else:
            raise NotImplementedError(f"Unsupported platform: {self.system}")
            
        analysis['processes'] = processes
        
        # Categorize processes
        for proc in processes:
            # Add user data directory to set
            if proc['user_data_dir']:
                analysis['user_data_dirs'].add(proc['user_data_dir'])
            
            # Categorize as main or child process
            if self._is_main_process(proc):
                analysis['main_processes'].append(proc)
            else:
                process_type = proc.get('process_type', 'unknown')
                analysis['child_processes'][process_type].append(proc)
                
            # Collect profiles
            if proc['user_data_dir'] and proc.get('profiles'):
                analysis['profiles'].update(proc['profiles'])
                
        return analysis
    
    def _is_main_process(self, proc: Dict) -> bool:
        """
        Determine if a process is a main Chrome process.
        
        Args:
            proc: Process dictionary
            
        Returns:
            True if main process, False otherwise
        """
        # Main process typically doesn't have --type parameter
        return '--type=' not in proc['args']
    
    def _analyze_macos_processes(self) -> List[Dict]:
        """Analyze Chrome processes on macOS."""
        processes = []
        try:
            # Get all Chrome-related processes with full command line
            result = subprocess.run(
                ["ps", "-ax", "-o", "pid,ppid,comm,args"],
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if 'Google Chrome' in line and 'grep' not in line:
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        pid = parts[0]
                        ppid = parts[1]
                        comm = parts[2]
                        args = parts[3]
                        
                        process_info = {
                            'pid': pid,
                            'ppid': ppid,
                            'command': comm,
                            'args': args,
                            'process_type': self._extract_process_type(args),
                            'user_data_dir': self._extract_user_data_dir(args),
                            'profiles': []
                        }
                        
                        # Get profiles if user data directory is available
                        if process_info['user_data_dir']:
                            process_info['profiles'] = self._get_profile_directories(process_info['user_data_dir'])
                            
                        processes.append(process_info)
                            
        except subprocess.CalledProcessError as e:
            print(f"Error analyzing macOS processes: {e}", file=sys.stderr)
            
        return processes
    
    def _analyze_windows_processes(self) -> List[Dict]:
        """Analyze Chrome processes on Windows."""
        processes = []
        try:
            # Use PowerShell to get Chrome processes with command line arguments
            cmd = [
                "powershell",
                "-Command",
                "Get-WmiObject Win32_Process -Filter \"Name='chrome.exe'\" | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                try:
                    process_data = json.loads(result.stdout)
                    # Handle both single process and array of processes
                    if isinstance(process_data, dict):
                        process_data = [process_data]
                    
                    for proc in process_data:
                        command_line = proc.get('CommandLine', '')
                        if command_line:
                            process_info = {
                                'pid': str(proc.get('ProcessId', '')),
                                'ppid': str(proc.get('ParentProcessId', '')),
                                'command': 'chrome.exe',
                                'args': command_line,
                                'process_type': self._extract_process_type(command_line),
                                'user_data_dir': self._extract_user_data_dir(command_line),
                                'profiles': []
                            }
                            
                            # Get profiles if user data directory is available
                            if process_info['user_data_dir']:
                                process_info['profiles'] = self._get_profile_directories(process_info['user_data_dir'])
                                
                            processes.append(process_info)
                except json.JSONDecodeError:
                    pass
                    
        except subprocess.CalledProcessError as e:
            print(f"Error analyzing Windows processes: {e}", file=sys.stderr)
            
        return processes
    
    def _analyze_linux_processes(self) -> List[Dict]:
        """Analyze Chrome processes on Linux."""
        processes = []
        try:
            # Get all Chrome-related processes with full command line
            result = subprocess.run(
                ["ps", "-eo", "pid,ppid,comm,args"],
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if ('chrome' in line or 'chromium' in line) and 'grep' not in line:
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        pid = parts[0]
                        ppid = parts[1]
                        comm = parts[2]
                        args = parts[3]
                        
                        process_info = {
                            'pid': pid,
                            'ppid': ppid,
                            'command': comm,
                            'args': args,
                            'process_type': self._extract_process_type(args),
                            'user_data_dir': self._extract_user_data_dir(args),
                            'profiles': []
                        }
                        
                        # Get profiles if user data directory is available
                        if process_info['user_data_dir']:
                            process_info['profiles'] = self._get_profile_directories(process_info['user_data_dir'])
                            
                        processes.append(process_info)
                            
        except subprocess.CalledProcessError as e:
            print(f"Error analyzing Linux processes: {e}", file=sys.stderr)
            
        return processes
    
    def _extract_process_type(self, args: str) -> str:
        """
        Extract process type from process arguments.
        
        Args:
            args: Command line arguments string
            
        Returns:
            Process type or 'main' for main process
        """
        # Look for --type parameter
        match = re.search(r'--type=([^\s]+)', args)
        if match:
            return match.group(1)
        return 'main'
    
    def _extract_user_data_dir(self, args: str) -> Optional[str]:
        """
        Extract user data directory from process arguments.
        
        Args:
            args: Command line arguments string
            
        Returns:
            User data directory path or None if not found
        """
        # Look for --user-data-dir parameter
        match = re.search(r'--user-data-dir[=\s]+("[^"]+"|[^\s]+)', args)
        if match:
            dir_path = match.group(1).strip('"')
            return os.path.expanduser(dir_path)
        
        # If no explicit user data dir, return default based on platform
        return self._get_default_user_data_dir()
    
    def _get_default_user_data_dir(self) -> Optional[str]:
        """
        Get platform-specific default user data directory.
        
        Returns:
            Default user data directory path or None
        """
        system = self.system
        home = os.path.expanduser("~")
        
        if system == "darwin":  # macOS
            return os.path.join(home, "Library", "Application Support", "Google", "Chrome")
        elif system == "windows":
            return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
        elif system == "linux":
            return os.path.join(home, ".config", "google-chrome")
        
        return None
    
    def _get_profile_directories(self, user_data_dir: str) -> List[str]:
        """
        Get all profile directories within user data directory.
        
        Args:
            user_data_dir: User data directory path
            
        Returns:
            List of profile directory names
        """
        profiles = []
        
        if not self._validate_directory(user_data_dir):
            return profiles
            
        try:
            for item in os.listdir(user_data_dir):
                item_path = os.path.join(user_data_dir, item)
                if os.path.isdir(item_path):
                    # Profile directories typically start with "Profile " or are "Default"
                    if item.startswith("Profile ") or item == "Default" or item.startswith("Guest "):
                        profiles.append(item)
        except OSError:
            pass
            
        return profiles
    
    def _validate_directory(self, dir_path: str) -> bool:
        """
        Validate if a directory exists and is accessible.
        
        Args:
            dir_path: Directory path to validate
            
        Returns:
            True if directory exists and is accessible, False otherwise
        """
        try:
            return os.path.isdir(dir_path) and os.access(dir_path, os.R_OK)
        except:
            return False


def print_analysis(analysis: Dict):
    """Print formatted analysis results."""
    print(f"Chrome Process Analysis Report")
    print(f"=============================")
    print(f"System: {analysis['system']}")
    print(f"Total Processes: {len(analysis['processes'])}")
    print(f"Main Processes: {len(analysis['main_processes'])}")
    print(f"User Data Directories: {len(analysis['user_data_dirs'])}")
    print(f"Profiles Found: {len(analysis['profiles'])}")
    
    print(f"\nUser Data Directories:")
    for i, dir_path in enumerate(analysis['user_data_dirs'], 1):
        print(f"  {i}. {dir_path}")
        if not os.path.exists(dir_path):
            print(f"     [WARNING] Directory does not exist!")
        elif not os.access(dir_path, os.R_OK):
            print(f"     [WARNING] Directory not readable!")
    
    print(f"\nProfiles:")
    for i, profile in enumerate(sorted(analysis['profiles']), 1):
        print(f"  {i}. {profile}")
    
    print(f"\nMain Processes:")
    for i, proc in enumerate(analysis['main_processes'], 1):
        print(f"  {i}. PID: {proc['pid']}, PPID: {proc['ppid']}")
        print(f"     Command: {proc['command']}")
        print(f"     User Data Dir: {proc['user_data_dir'] or 'Default'}")
        if proc['profiles']:
            print(f"     Profiles: {', '.join(proc['profiles'])}")
    
    print(f"\nChild Processes by Type:")
    for process_type, processes in analysis['child_processes'].items():
        print(f"  {process_type} ({len(processes)} processes):")
        for proc in processes[:5]:  # Show first 5 only
            print(f"    PID: {proc['pid']}, PPID: {proc['ppid']}")
        if len(processes) > 5:
            print(f"    ... and {len(processes) - 5} more")


def main():
    """Main function to demonstrate Chrome process analysis."""
    analyzer = ChromeProcessAnalyzer()
    
    print(f"Analyzing Chrome processes on {platform.system()}...")
    
    try:
        analysis = analyzer.analyze_processes()
        print_analysis(analysis)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
