#!/usr/bin/env python3
"""
Cross-platform Chrome process and user data directory detector.

This script detects running Chrome/Chromium processes and extracts their user data directories,
handling platform-specific variations and edge cases.
"""

import os
import sys
import subprocess
import re
import json
import platform
from typing import List, Dict, Optional, Tuple


class ChromeProcessDetector:
    """Cross-platform Chrome process detector."""
    
    def __init__(self):
        self.system = platform.system().lower()
        
    def detect_processes(self) -> List[Dict]:
        """
        Detect all Chrome/Chromium processes on the system.
        
        Returns:
            List of dictionaries containing process information
        """
        processes = []
        
        if self.system == "darwin":  # macOS
            processes = self._detect_macos_processes()
        elif self.system == "windows":
            processes = self._detect_windows_processes()
        elif self.system == "linux":
            processes = self._detect_linux_processes()
        else:
            raise NotImplementedError(f"Unsupported platform: {self.system}")
            
        return processes
    
    def _detect_macos_processes(self) -> List[Dict]:
        """Detect Chrome processes on macOS."""
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
                    parts = line.split()
                    if len(parts) >= 4:
                        pid = parts[0]
                        ppid = parts[1]
                        comm = parts[2]
                        args = ' '.join(parts[3:])
                        
                        # Skip renderer processes and helpers
                        if '(Renderer)' not in comm and 'Helper' not in comm and 'crashpad' not in args:
                            process_info = {
                                'pid': pid,
                                'ppid': ppid,
                                'command': comm,
                                'args': args,
                                'user_data_dir': self._extract_user_data_dir(args)
                            }
                            processes.append(process_info)
                            
        except subprocess.CalledProcessError as e:
            print(f"Error detecting macOS processes: {e}", file=sys.stderr)
            
        return processes
    
    def _detect_windows_processes(self) -> List[Dict]:
        """Detect Chrome processes on Windows."""
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
                        # Only consider main Chrome processes (not renderer processes)
                        command_line = proc.get('CommandLine', '')
                        if command_line and '--type=' not in command_line:
                            process_info = {
                                'pid': str(proc.get('ProcessId', '')),
                                'ppid': str(proc.get('ParentProcessId', '')),
                                'command': 'chrome.exe',
                                'args': command_line,
                                'user_data_dir': self._extract_user_data_dir(command_line)
                            }
                            processes.append(process_info)
                except json.JSONDecodeError:
                    pass
                    
        except subprocess.CalledProcessError as e:
            print(f"Error detecting Windows processes: {e}", file=sys.stderr)
            
        return processes
    
    def _detect_linux_processes(self) -> List[Dict]:
        """Detect Chrome processes on Linux."""
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
                        
                        # Skip renderer processes and helpers
                        if '--type=' not in args:
                            process_info = {
                                'pid': pid,
                                'ppid': ppid,
                                'command': comm,
                                'args': args,
                                'user_data_dir': self._extract_user_data_dir(args)
                            }
                            processes.append(process_info)
                            
        except subprocess.CalledProcessError as e:
            print(f"Error detecting Linux processes: {e}", file=sys.stderr)
            
        return processes
    
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
    
    def validate_directory(self, dir_path: str) -> bool:
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
    
    def get_profile_directories(self, user_data_dir: str) -> List[str]:
        """
        Get all profile directories within user data directory.
        
        Args:
            user_data_dir: User data directory path
            
        Returns:
            List of profile directory paths
        """
        profiles = []
        
        if not self.validate_directory(user_data_dir):
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


def main():
    """Main function to demonstrate Chrome process detection."""
    detector = ChromeProcessDetector()
    
    print(f"Detecting Chrome processes on {platform.system()}...")
    print("=" * 50)
    
    processes = detector.detect_processes()
    
    if not processes:
        print("No Chrome processes found.")
        return
    
    for i, proc in enumerate(processes, 1):
        print(f"\n{i}. Process PID: {proc['pid']}")
        print(f"   Parent PID: {proc['ppid']}")
        print(f"   Command: {proc['command']}")
        print(f"   User Data Directory: {proc['user_data_dir'] or 'Not specified (using default)'}")
        
        # Validate directory
        if proc['user_data_dir']:
            if detector.validate_directory(proc['user_data_dir']):
                print(f"   Status: Accessible")
                # Show profile directories
                profiles = detector.get_profile_directories(proc['user_data_dir'])
                if profiles:
                    print(f"   Profiles: {', '.join(profiles)}")
            else:
                print(f"   Status: Directory not accessible or doesn't exist")
        else:
            default_dir = detector._get_default_user_data_dir()
            if default_dir and detector.validate_directory(default_dir):
                print(f"   Default Directory: {default_dir}")
                print(f"   Status: Accessible (default)")
                # Show profile directories
                profiles = detector.get_profile_directories(default_dir)
                if profiles:
                    print(f"   Profiles: {', '.join(profiles)}")
            else:
                print(f"   Status: Default directory not accessible")


if __name__ == "__main__":
    main()
