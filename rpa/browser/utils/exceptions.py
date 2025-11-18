"""
浏览器相关异常类
"""

from typing import List


class LoginRequiredError(Exception):
    """
    登录态缺失异常
    
    当检测到必需域名未登录时抛出此异常
    """
    
    def __init__(self, missing_domains: List[str], profile: str = None, message: str = None):
        """
        初始化异常
        
        Args:
            missing_domains: 未登录的域名列表
            profile: 检查的 Profile 名称
            message: 自定义错误消息
        """
        self.missing_domains = missing_domains
        self.profile = profile
        
        if message:
            self.message = message
        else:
            domains_str = "、".join(missing_domains)
            profile_str = f" (Profile: {profile})" if profile else ""
            self.message = (
                f"❌ 检测到以下域名未登录{profile_str}: {domains_str}\n\n"
                f"📋 请按以下步骤操作：\n"
                f"1. 在 Edge 浏览器中打开以下网站并登录：\n"
            )
            for domain in missing_domains:
                self.message += f"   - https://{domain}\n"
            self.message += (
                f"\n2. 登录完成后，重新运行程序\n"
                f"\n💡 提示：确保浏览器使用了调试端口启动（--remote-debugging-port=9222）"
            )
        
        super().__init__(self.message)
    
    def __str__(self):
        return self.message
