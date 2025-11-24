"""
浏览器检测工具

用于检测当前运行的浏览器进程和 Profile 信息
"""

import os
import platform

import subprocess
from typing import Optional, Dict, List, Any
import logging


class BrowserDetector:
    """浏览器检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        
    def detect_active_profile(self) -> Optional[str]:
        """
        检测最近使用的浏览器 Profile

        Returns:
            Profile 名称，如 "Profile 1"、"Default" 等，未找到返回 None
        """
        try:
            user_data_dir = self._get_edge_user_data_dir()
            if not user_data_dir or not os.path.exists(user_data_dir):
                self.logger.warning(f"Edge 用户数据目录不存在: {user_data_dir}")
                return None

            # 获取所有 Profile（已按最近使用时间排序）
            profiles = self._list_profiles(user_data_dir)
            self.logger.info(f"🔍 发现 {len(profiles)} 个 Profile: {profiles}")

            if not profiles:
                self.logger.warning("⚠️ 未找到任何 Profile")
                return None

            # 返回最近使用的 Profile
            most_recent_profile = profiles[0]
            self.logger.info(f"✅ 使用最近使用的 Profile: {most_recent_profile}")
            return most_recent_profile
            
        except Exception as e:
            self.logger.error(f"❌ 检测 Profile 失败: {e}")
            return None
    
    def _get_edge_user_data_dir(self) -> Optional[str]:
        """获取 Edge 浏览器用户数据目录"""
        import os
        if self.system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/Microsoft Edge")
        elif self.system == "Windows":
            # 🔧 修复：使用Windows风格的路径格式以匹配测试期望
            return os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")
        elif self.system == "Linux":
            return os.path.expanduser("~/.config/microsoft-edge")
        else:
            return None
    
    def _list_profiles(self, user_data_dir: str) -> List[str]:
        """列出所有 Profile"""
        profiles = []
        
        try:
            # 检查 Default Profile
            if os.path.exists(os.path.join(user_data_dir, "Default")):
                profiles.append("Default")
            
            # 检查 Profile 1, 2, 3...
            for i in range(1, 10):
                profile_name = f"Profile {i}"
                profile_path = os.path.join(user_data_dir, profile_name)
                if os.path.exists(profile_path):
                    profiles.append(profile_name)
            
            # 按最近修改时间排序（最近使用的在前）
            profiles.sort(
                key=lambda p: os.path.getmtime(os.path.join(user_data_dir, p)),
                reverse=True
            )
            
        except Exception as e:
            self.logger.error(f"列出 Profile 失败: {e}")
        
        return profiles
    
    def is_profile_locked(self, profile_path: str) -> bool:
        """
        检查 Profile 是否被锁定

        Args:
            profile_path: Profile 的完整路径

        Returns:
            True 表示被锁定，False 表示未锁定
        """
        try:
            if not os.path.exists(profile_path):
                return False

            # 检查锁定文件
            # Chromium/Edge 使用多种锁定机制
            lock_files = [
                "Singleton Lock",  # Linux/macOS
                "lockfile",        # Linux
                "SingletonLock",   # Windows
            ]

            for lock_file in lock_files:
                lock_path = os.path.join(profile_path, lock_file)
                if os.path.exists(lock_path):
                    self.logger.debug(f"🔒 发现锁定文件: {lock_path}")
                    return True

            return False

        except Exception as e:
            self.logger.warning(f"检查 Profile 锁定状态失败: {e}")
            # 出错时保守处理，假设未锁定
            return False

    def is_profile_available(self, user_data_dir: str, profile_name: str) -> bool:
        """
        检查 Profile 是否可用（存在且未被锁定）

        Args:
            user_data_dir: 用户数据目录
            profile_name: Profile 名称

        Returns:
            True 表示可用，False 表示不可用
        """
        try:
            profile_path = os.path.join(user_data_dir, profile_name)

            # 检查 Profile 目录是否存在
            if not os.path.exists(profile_path):
                self.logger.warning(f"⚠️ Profile 不存在: {profile_path}")
                return False

            # 检查是否可访问（读写权限）
            if not os.access(profile_path, os.R_OK | os.W_OK):
                self.logger.warning(f"⚠️ Profile 无访问权限: {profile_path}")
                return False

            # 检查是否被锁定
            if self.is_profile_locked(profile_path):
                self.logger.warning(f"🔒 Profile 已被锁定: {profile_path}")
                return False

            self.logger.info(f"✅ Profile 可用: {profile_path}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 检查 Profile 可用性失败: {e}")
            return False


    def is_browser_running(self) -> bool:
        """检查 Edge 浏览器是否正在运行"""
        try:
            if self.system == "Darwin":  # macOS
                result = subprocess.run(
                    ["pgrep", "-f", "Microsoft Edge"],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            elif self.system == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq msedge.exe"],
                    capture_output=True,
                    text=True
                )
                return "msedge.exe" in result.stdout
            elif self.system == "Linux":
                result = subprocess.run(
                    ["pgrep", "-f", "microsoft-edge"],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            else:
                return False

        except Exception as e:
            self.logger.error(f"检查浏览器进程失败: {e}")
            return False

    def kill_browser_processes(self, force: bool = True) -> bool:
        """
        清理僵尸浏览器进程

        Args:
            force: 是否强制杀死进程（使用 SIGKILL/-9）

        Returns:
            True 表示成功清理，False 表示清理失败
        """
        try:
            self.logger.info("🧹 开始清理浏览器进程...")

            if self.system == "Darwin":  # macOS
                # 使用 pkill 命令清理 Edge 进程
                signal_flag = "-9" if force else "-15"
                result = subprocess.run(
                    ["pkill", signal_flag, "-f", "Microsoft Edge"],
                    capture_output=True,
                    text=True
                )
                # pkill 返回 0 表示成功杀死进程，返回 1 表示没有找到进程
                success = result.returncode in [0, 1]

            elif self.system == "Windows":
                # 使用 taskkill 命令清理 Edge 进程
                force_flag = "/F" if force else ""
                result = subprocess.run(
                    ["taskkill", force_flag, "/IM", "msedge.exe", "/T"],
                    capture_output=True,
                    text=True
                )
                success = result.returncode == 0 or "not found" in result.stdout.lower()

            elif self.system == "Linux":
                # 使用 pkill 命令清理 Edge 进程
                signal_flag = "-9" if force else "-15"
                result = subprocess.run(
                    ["pkill", signal_flag, "-f", "microsoft-edge"],
                    capture_output=True,
                    text=True
                )
                success = result.returncode in [0, 1]

            else:
                self.logger.warning(f"不支持的操作系统: {self.system}")
                return False

            if success:
                self.logger.info("✅ 浏览器进程清理完成")
                # 等待进程完全退出
                import time
                time.sleep(1)
                return True
            else:
                self.logger.warning("⚠️ 浏览器进程清理可能失败")
                return False

        except Exception as e:
            self.logger.error(f"❌ 清理浏览器进程失败: {e}")
            return False

    def wait_for_profile_unlock(self, profile_path: str, max_wait_seconds: int = 5) -> bool:
        """
        等待 Profile 解锁

        Args:
            profile_path: Profile 的完整路径
            max_wait_seconds: 最大等待时间（秒）

        Returns:
            True 表示 Profile 已解锁，False 表示仍然被锁定
        """
        try:
            import time
            waited = 0
            check_interval = 0.5  # 每 0.5 秒检查一次

            self.logger.info(f"⏳ 等待 Profile 解锁（最多 {max_wait_seconds} 秒）...")

            while waited < max_wait_seconds:
                if not self.is_profile_locked(profile_path):
                    self.logger.info(f"✅ Profile 已解锁（等待了 {waited:.1f} 秒）")
                    return True

                time.sleep(check_interval)
                waited += check_interval

            self.logger.warning(f"⚠️ Profile 仍然被锁定（已等待 {max_wait_seconds} 秒）")
            return False

        except Exception as e:
            self.logger.error(f"❌ 等待 Profile 解锁失败: {e}")
            return False

    def get_browser_info(self) -> Dict[str, Any]:
        """
        获取浏览器信息

        Returns:
            包含浏览器信息的字典
        """
        info = {
            "is_running": self.is_browser_running(),
            "user_data_dir": self._get_edge_user_data_dir(),
            "active_profile": None,
            "all_profiles": []
        }

        if info["user_data_dir"] and os.path.exists(info["user_data_dir"]):
            info["all_profiles"] = self._list_profiles(info["user_data_dir"])
            info["active_profile"] = self.detect_active_profile()

        return info




# 便捷函数
def detect_active_profile() -> Optional[str]:
    """
    检测最近使用的浏览器 Profile

    Returns:
        Profile 名称或 None
    """
    detector = BrowserDetector()
    return detector.detect_active_profile()


def get_browser_info() -> Dict[str, Any]:
    """获取浏览器信息"""
    detector = BrowserDetector()
    return detector.get_browser_info()