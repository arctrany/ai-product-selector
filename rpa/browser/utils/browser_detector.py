"""
浏览器检测工具

用于检测当前运行的浏览器进程和 Profile 信息
"""

import os
import platform
import sqlite3
import subprocess
from typing import Optional, Dict, List
import logging


class BrowserDetector:
    """浏览器检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        
    def detect_active_profile(self, target_domain: str = "seerfar.cn") -> Optional[str]:
        """
        检测有指定域名登录态的 Profile
        
        Args:
            target_domain: 目标域名，用于验证登录态
            
        Returns:
            Profile 名称，如 "Profile 1"、"Default" 等，未找到返回 None
        """
        try:
            user_data_dir = self._get_edge_user_data_dir()
            if not user_data_dir or not os.path.exists(user_data_dir):
                self.logger.warning(f"Edge 用户数据目录不存在: {user_data_dir}")
                return None
            
            # 获取所有 Profile
            profiles = self._list_profiles(user_data_dir)
            self.logger.info(f"🔍 发现 {len(profiles)} 个 Profile: {profiles}")
            
            # 检查每个 Profile 是否有目标域名的登录态
            for profile in profiles:
                if self._has_login_cookies(user_data_dir, profile, target_domain):
                    self.logger.info(f"✅ 找到有 {target_domain} 登录态的 Profile: {profile}")
                    return profile
            
            self.logger.warning(f"⚠️ 未找到有 {target_domain} 登录态的 Profile")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 检测 Profile 失败: {e}")
            return None
    
    def _get_edge_user_data_dir(self) -> Optional[str]:
        """获取 Edge 浏览器用户数据目录"""
        if self.system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/Microsoft Edge")
        elif self.system == "Windows":
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
    
    def _has_login_cookies(self, user_data_dir: str, profile: str, domain: str) -> bool:
        """
        检查指定 Profile 是否有目标域名的登录 Cookies
        
        Args:
            user_data_dir: 用户数据目录
            profile: Profile 名称
            domain: 目标域名
            
        Returns:
            是否有登录态
        """
        cookies_db = os.path.join(user_data_dir, profile, "Cookies")
        
        if not os.path.exists(cookies_db):
            self.logger.debug(f"Cookies 文件不存在: {cookies_db}")
            return False
        
        try:
            # 创建临时副本以避免数据库锁定
            import tempfile
            import shutil
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
                tmp_cookies_db = tmp_file.name
            
            try:
                shutil.copy2(cookies_db, tmp_cookies_db)
                
                # 查询 Cookies
                conn = sqlite3.connect(tmp_cookies_db)
                cursor = conn.cursor()
                
                # 查找包含目标域名的 cookies
                cursor.execute(
                    "SELECT name FROM cookies WHERE host_key LIKE ? LIMIT 1",
                    (f"%{domain}%",)
                )
                
                result = cursor.fetchone()
                conn.close()
                
                has_cookies = result is not None
                if has_cookies:
                    self.logger.debug(f"✅ {profile} 有 {domain} 的 cookies")
                else:
                    self.logger.debug(f"❌ {profile} 没有 {domain} 的 cookies")
                
                return has_cookies
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(tmp_cookies_db)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"检查 Cookies 失败: {e}")
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
    
    def get_browser_info(self) -> Dict[str, any]:
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

    def check_domain_login(self, profile: str, domain: str) -> Dict[str, any]:
        """
        检查指定 Profile 对某个域名的登录状态

        Args:
            profile: Profile 名称
            domain: 域名

        Returns:
            包含登录状态信息的字典
        """
        user_data_dir = self._get_edge_user_data_dir()
        if not user_data_dir or not os.path.exists(user_data_dir):
            return {
                "domain": domain,
                "has_login": False,
                "cookie_count": 0,
                "error": "用户数据目录不存在"
            }

        cookies_db = os.path.join(user_data_dir, profile, "Cookies")

        if not os.path.exists(cookies_db):
            return {
                "domain": domain,
                "has_login": False,
                "cookie_count": 0,
                "error": "Cookies 文件不存在"
            }

        try:
            import tempfile
            import shutil

            with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
                tmp_cookies_db = tmp_file.name

            try:
                shutil.copy2(cookies_db, tmp_cookies_db)

                conn = sqlite3.connect(tmp_cookies_db)
                cursor = conn.cursor()

                # 查询该域名的所有 cookies
                cursor.execute(
                    "SELECT name, value, expires_utc FROM cookies WHERE host_key LIKE ?",
                    (f"%{domain}%",)
                )

                cookies = cursor.fetchall()
                conn.close()

                return {
                    "domain": domain,
                    "has_login": len(cookies) > 0,
                    "cookie_count": len(cookies),
                    "error": None
                }

            finally:
                try:
                    os.unlink(tmp_cookies_db)
                except:
                    pass

        except Exception as e:
            return {
                "domain": domain,
                "has_login": False,
                "cookie_count": 0,
                "error": str(e)
            }

    def analyze_all_profiles_login_status(self, domains: List[str]) -> Dict[str, Dict[str, any]]:
        """
        分析所有 Profile 对指定域名列表的登录状态

        Args:
            domains: 需要检查的域名列表

        Returns:
            {
                "Profile 1": {
                    "seerfar.cn": {"has_login": True, "cookie_count": 3},
                    "www.maozierp.com": {"has_login": True, "cookie_count": 1}
                },
                ...
            }
        """
        user_data_dir = self._get_edge_user_data_dir()
        if not user_data_dir or not os.path.exists(user_data_dir):
            self.logger.error("用户数据目录不存在")
            return {}

        profiles = self._list_profiles(user_data_dir)
        result = {}

        for profile in profiles:
            profile_status = {}
            for domain in domains:
                status = self.check_domain_login(profile, domain)
                profile_status[domain] = {
                    "has_login": status["has_login"],
                    "cookie_count": status["cookie_count"]
                }
            result[profile] = profile_status

        return result

    def validate_required_logins(self, required_domains: List[str]) -> tuple[bool, List[str], str]:
        """
        验证所有必需域名的登录态（AND 逻辑）

        Args:
            required_domains: 必需登录的域名列表

        Returns:
            (是否全部已登录, 未登录的域名列表, 使用的 Profile)
        """
        if not required_domains:
            self.logger.info("未配置必需登录域名，跳过检查")
            return True, [], None

        user_data_dir = self._get_edge_user_data_dir()
        if not user_data_dir or not os.path.exists(user_data_dir):
            self.logger.error("用户数据目录不存在")
            return False, required_domains, None

        profiles = self._list_profiles(user_data_dir)

        # 尝试找到一个所有域名都已登录的 Profile
        for profile in profiles:
            missing_domains = []

            for domain in required_domains:
                if not self._has_login_cookies(user_data_dir, profile, domain):
                    missing_domains.append(domain)

            # 如果这个 Profile 所有域名都已登录
            if not missing_domains:
                self.logger.info(f"✅ {profile} 所有必需域名都已登录: {required_domains}")
                return True, [], profile

        # 没有找到满足条件的 Profile，返回第一个 Profile 的缺失域名
        if profiles:
            first_profile = profiles[0]
            missing_domains = []
            for domain in required_domains:
                if not self._has_login_cookies(user_data_dir, first_profile, domain):
                    missing_domains.append(domain)

            self.logger.warning(f"⚠️ {first_profile} 缺少以下域名的登录态: {missing_domains}")
            return False, missing_domains, first_profile

        # 没有任何 Profile
        self.logger.error("未找到任何 Profile")
        return False, required_domains, None

    def print_login_status_report(self, domains: List[str]) -> None:
        """
        打印所有 Profile 的登录状态详细报告

        Args:
            domains: 需要检查的域名列表
        """
        print("\n" + "="*80)
        print("📊 浏览器登录状态详细报告")
        print("="*80)

        status = self.analyze_all_profiles_login_status(domains)

        if not status:
            print("❌ 未找到任何 Profile 或用户数据目录不存在")
            return

        for profile, domain_status in status.items():
            print(f"\n🔹 {profile}")
            print("-" * 60)

            for domain, info in domain_status.items():
                status_icon = "✅" if info["has_login"] else "❌"
                cookie_info = f"({info['cookie_count']} cookies)" if info["has_login"] else ""
                print(f"  {status_icon} {domain:30s} {cookie_info}")

        print("\n" + "="*80)


# 便捷函数
def detect_active_profile(target_domain: str = "seerfar.cn") -> Optional[str]:
    """
    检测有指定域名登录态的 Profile
    
    Args:
        target_domain: 目标域名
        
    Returns:
        Profile 名称或 None
    """
    detector = BrowserDetector()
    return detector.detect_active_profile(target_domain)


def get_browser_info() -> Dict[str, any]:
    """获取浏览器信息"""
    detector = BrowserDetector()
    return detector.get_browser_info()
