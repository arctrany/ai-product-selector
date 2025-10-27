#!/usr/bin/env python3
"""
Cross-platform Workflow Engine Server Control Script
Usage: python workflow_server.py [start|stop|restart|status|install|logs|apps|test]
"""

import os
import sys
import time
import signal
import subprocess
import platform
import psutil
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict

# Import Windows compatibility utilities
try:
    from src_new.utils.windows_compat import (
        normalize_path, is_windows, fix_command_for_windows
    )
except ImportError:
    # Fallback implementations if windows_compat is not available
    def normalize_path(path):
        return Path(path).resolve()

    def is_windows():
        return platform.system().lower() == "windows"

    def fix_command_for_windows(command):
        return command

class WorkflowServerManager:
    """Cross-platform workflow server manager"""

    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.project_dir = self.script_dir.parent

        # Load environment variables
        self.load_environment_variables()

        self.server_module = "src_new.workflow_engine.api.server"
        self.pid_file = normalize_path(self.project_dir / ".workflow_server.pid")
        self.log_file = normalize_path(self.project_dir / "workflow_server.log")
        self.src_dir = normalize_path(self.project_dir / os.getenv('WORKFLOW_SOURCE_DIR', 'src_new'))
        self.requirements_file = normalize_path(self.src_dir / "requirements.txt")
        self.ports = [8000, 8888, 8001, 8889]
        self.server_port = int(os.getenv('WORKFLOW_PORT', '8889'))

    def load_environment_variables(self) -> None:
        """Load environment variables from .env file if it exists"""
        env_file = normalize_path(self.script_dir / '.env')
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key and not os.getenv(key):
                                os.environ[key] = value
                print(f"✓ Environment variables loaded from {env_file}")
            except Exception as e:
                print(f"⚠ Warning: Could not load environment variables: {e}")
        else:
            print(f"ℹ No .env file found at {env_file}")

    def print_status(self, message: str):
        """Print status message"""
        print(f"\033[32m[INFO]\033[0m {message}")

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"\033[33m[WARN]\033[0m {message}")

    def print_error(self, message: str):
        """Print error message"""
        print(f"\033[31m[ERROR]\033[0m {message}")

    def is_running(self) -> bool:
        """Check if server is running"""
        if not self.pid_file.exists():
            return False

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process exists and is running
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                if process.is_running():
                    return True

            # Clean up stale PID file
            self.pid_file.unlink(missing_ok=True)
            return False

        except (ValueError, psutil.NoSuchProcess, PermissionError):
            self.pid_file.unlink(missing_ok=True)
            return False

    def get_pid(self) -> Optional[int]:
        """Get server PID if running"""
        if not self.pid_file.exists():
            return None

        try:
            with open(self.pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, FileNotFoundError):
            return None

    def kill_port_processes(self):
        """Kill processes using our ports - cross-platform implementation"""
        self.print_status(f"Cleaning up ports {', '.join(map(str, self.ports))}...")

        for port in self.ports:
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                        try:
                            process = psutil.Process(conn.pid)
                            process.terminate()
                            time.sleep(0.5)
                            if process.is_running():
                                process.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            except (psutil.AccessDenied, AttributeError):
                # Platform-specific fallback
                if is_windows():
                    try:
                        # Windows: Use netstat and taskkill
                        result = subprocess.run([
                            "netstat", "-ano", "-p", "TCP"
                        ], capture_output=True, text=True, check=False)

                        if result.stdout:
                            lines = result.stdout.split('\n')
                            for line in lines:
                                if f":{port}" in line and "LISTENING" in line:
                                    parts = line.split()
                                    if len(parts) >= 5:
                                        pid = parts[-1]
                                        try:
                                            subprocess.run([
                                                "taskkill", "/F", "/PID", pid
                                            ], capture_output=True, check=False)
                                        except Exception:
                                            pass
                    except FileNotFoundError:
                        pass
                else:
                    try:
                        # Unix-like systems: Use lsof and kill
                        result = subprocess.run([
                            "lsof", "-ti", f":{port}"
                        ], capture_output=True, text=True, check=False)

                        if result.stdout.strip():
                            pids = result.stdout.strip().split('\n')
                            for pid in pids:
                                try:
                                    if is_windows():
                                        # Windows doesn't have SIGTERM
                                        os.kill(int(pid), signal.SIGTERM if hasattr(signal, 'SIGTERM') else signal.SIGINT)
                                    else:
                                        os.kill(int(pid), signal.SIGTERM)
                                except (ValueError, ProcessLookupError, PermissionError):
                                    pass
                    except FileNotFoundError:
                        pass

    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        self.print_status("Installing Python dependencies...")

        # Check Python version
        if sys.version_info < (3, 8):
            self.print_error("Python 3.8+ is required")
            return False

        # Check if requirements file exists
        if not self.requirements_file.exists():
            self.print_error(f"Requirements file not found: {self.requirements_file}")
            return False

        try:
            # Install requirements
            self.print_status("Installing from requirements.txt...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)
            ], check=True, capture_output=True, text=True)

            # Install Playwright browsers
            self.print_status("Installing Playwright browsers...")
            try:
                subprocess.run([
                    sys.executable, "-m", "playwright", "install"
                ], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                self.print_warning("Failed to install Playwright browsers automatically")
                self.print_status("You may need to run 'python -m playwright install' manually")

            self.print_status("Dependencies installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to install dependencies: {e}")
            if e.stderr:
                self.print_error(f"Error details: {e.stderr}")
            return False

    def start_server(self) -> bool:
        """Start the workflow server"""
        if self.is_running():
            pid = self.get_pid()
            self.print_warning(f"Server is already running (PID: {pid})")
            return False

        self.print_status("Starting Workflow Engine Server...")

        # Kill any processes using our ports
        self.kill_port_processes()

        # Change to project directory (not src_new) for proper module resolution
        original_cwd = os.getcwd()
        try:
            os.chdir(self.project_dir)

            # Start server process
            with open(self.log_file, 'w') as log_f:
                if is_windows():
                    # Windows: Use CREATE_NEW_PROCESS_GROUP to avoid signal issues
                    process = subprocess.Popen([
                        sys.executable, "-m", self.server_module
                    ], stdout=log_f, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0)
                else:
                    # Unix-like systems: Standard process creation
                    process = subprocess.Popen([
                        sys.executable, "-m", self.server_module
                    ], stdout=log_f, stderr=subprocess.STDOUT)

            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))

            # Wait a moment and check if server started successfully
            time.sleep(3)

            if self.is_running():
                self.print_status(f"Server started successfully (PID: {process.pid})")
                self.print_status(f"Server running on: http://0.0.0.0:{self.server_port}")
                self.print_status(f"Log file: {self.log_file}")
                return True
            else:
                self.print_error("Failed to start server")
                self.print_error(f"Check log file: {self.log_file}")
                return False

        finally:
            os.chdir(original_cwd)

    def stop_server(self) -> bool:
        """Stop the workflow server - cross-platform implementation"""
        if not self.is_running():
            self.print_warning("Server is not running")
            return False

        pid = self.get_pid()
        self.print_status(f"Stopping server (PID: {pid})...")

        try:
            process = psutil.Process(pid)

            # Try graceful shutdown first
            if is_windows():
                # Windows: Use terminate() which sends SIGTERM equivalent
                process.terminate()
            else:
                # Unix-like systems: Send SIGTERM
                process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                self.print_warning("Forcing server shutdown...")
                process.kill()
                process.wait(timeout=5)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        # Clean up PID file
        self.pid_file.unlink(missing_ok=True)

        # Also clean up any remaining processes on our ports
        self.kill_port_processes()

        self.print_status("Server stopped")
        return True

    def restart_server(self) -> bool:
        """Restart the workflow server"""
        self.print_status("Restarting Workflow Engine Server...")
        self.stop_server()
        time.sleep(2)
        return self.start_server()

    def show_status(self):
        """Show server status"""
        if self.is_running():
            pid = self.get_pid()
            self.print_status(f"Server is running (PID: {pid})")
            self.print_status(f"Server URL: http://0.0.0.0:{self.server_port}")
            self.print_status(f"Apps page: http://localhost:{self.server_port}/apps")

            # Show port usage
            print("\nPort usage:")
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == self.server_port and conn.status == psutil.CONN_LISTEN:
                        print(f"Port {self.server_port}: In use by PID {conn.pid}")
                        break
                else:
                    print(f"Port {self.server_port}: Not in use")
            except (psutil.AccessDenied, AttributeError):
                print(f"Port {self.server_port}: Status unknown")

            # Show recent log entries
            if self.log_file.exists():
                print("\nRecent log entries:")
                try:
                    with open(self.log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-5:]:
                            print(line.rstrip())
                except Exception:
                    print("Could not read log file")
        else:
            self.print_warning("Server is not running")

    def show_logs(self):
        """Show server logs"""
        if not self.log_file.exists():
            self.print_error(f"Log file not found: {self.log_file}")
            return

        self.print_status("Showing server logs (Press Ctrl+C to exit):")
        try:
            # Follow log file
            with open(self.log_file, 'r') as f:
                # Go to end of file
                f.seek(0, 2)

                while True:
                    line = f.readline()
                    if line:
                        print(line.rstrip())
                    else:
                        time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nLog following stopped")

    def open_apps(self):
        """Open apps page in browser"""
        if not self.is_running():
            self.print_error("Server is not running. Start it first with: python workflow_server.py start")
            return

        url = f"http://localhost:{self.server_port}/apps"
        self.print_status("Opening apps page in browser...")

        try:
            webbrowser.open(url)
        except Exception:
            self.print_status(f"Please open: {url}")

    def test_apps(self):
        """Test and open application pages"""
        if not self.is_running():
            self.print_error("Server is not running. Start it first with: python workflow_server.py start")
            return

        self.print_status("Testing application pages...")

        base_url = f"http://localhost:{self.server_port}"

        self.print_status("Testing endpoints:")
        print(f"  Main page: {base_url}/")
        print(f"  Apps list: {base_url}/apps")
        print(f"  Sample app: {base_url}/apps/sample_app")
        print(f"  Sample console: {base_url}/console/sample_app")
        print(f"  API docs: {base_url}/docs")

        # Open key pages in browser
        self.print_status("Opening key pages in browser...")
        urls = [
            f"{base_url}/apps",
            f"{base_url}/apps/sample_app",
            f"{base_url}/console/sample_app"
        ]

        for url in urls:
            try:
                webbrowser.open(url)
                time.sleep(1)
            except Exception:
                print(f"Could not open: {url}")

def main():
    """Main entry point"""
    manager = WorkflowServerManager()

    if len(sys.argv) < 2:
        print("Usage: python workflow_server.py {start|stop|restart|status|install|logs|apps|test}")
        print()
        print("Commands:")
        print("  install - Install Python dependencies and Playwright browsers")
        print("  start   - Start the workflow engine server")
        print("  stop    - Stop the workflow engine server")
        print("  restart - Restart the workflow engine server")
        print("  status  - Show server status")
        print("  logs    - Show server logs (real-time)")
        print("  apps    - Open apps page in browser")
        print("  test    - Test and open all app pages")
        print()
        print(f"Server will run on: http://0.0.0.0:{manager.server_port}")
        print(f"Apps page: http://localhost:{manager.server_port}/apps")
        print()
        print("First time setup: python workflow_server.py install")
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        if command == "install":
            success = manager.install_dependencies()
            sys.exit(0 if success else 1)
        elif command == "start":
            success = manager.start_server()
            sys.exit(0 if success else 1)
        elif command == "stop":
            success = manager.stop_server()
            sys.exit(0 if success else 1)
        elif command == "restart":
            success = manager.restart_server()
            sys.exit(0 if success else 1)
        elif command == "status":
            manager.show_status()
        elif command == "logs":
            manager.show_logs()
        elif command == "apps":
            manager.open_apps()
        elif command == "test":
            manager.test_apps()
        else:
            manager.print_error(f"Unknown command: {command}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        manager.print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()