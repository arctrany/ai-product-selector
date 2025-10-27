"""
Chrome DevTools 集成分析工具
用于淘宝商品抓取的页面分析和网络监控

虽然 Chrome DevTools MCP 工具目前连接有问题，
但我们可以通过代码分析和模拟来提供解决方案
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

@dataclass
class NetworkRequest:
    """网络请求数据类"""
    url: str
    method: str
    status: int
    response_type: str
    size: int
    timing: Dict[str, float]
    headers: Dict[str, str]

@dataclass
class PageElement:
    """页面元素数据类"""
    tag_name: str
    selector: str
    text_content: str
    attributes: Dict[str, str]
    position: Dict[str, int]

@dataclass
class PageAnalysis:
    """页面分析结果"""
    url: str
    title: str
    load_time: float
    elements_count: int
    network_requests: List[NetworkRequest]
    product_elements: List[PageElement]
    anti_crawling_indicators: List[str]
    performance_metrics: Dict[str, Any]

class ChromeDevToolsAnalyzer:
    """Chrome DevTools 分析器"""
    
    def __init__(self, browser_service):
        """
        初始化分析器
        
        Args:
            browser_service: BrowserService 实例
        """
        self.browser_service = browser_service
        self.logger = logging.getLogger(__name__)
        
        # 淘宝特定的分析规则
        self.taobao_selectors = {
            'product_containers': [
                '[data-spm*="product"]',
                '[data-category="auctions"]',
                '.recommend-item',
                '.item',
                '.product-item'
            ],
            'anti_crawling_elements': [
                '.captcha',
                '#nc_1_n1z',
                '.verify-code',
                '.slider-verify'
            ]
        }
    
    async def analyze_page(self, url: str) -> PageAnalysis:
        """
        分析页面结构和性能
        
        Args:
            url: 要分析的页面URL
            
        Returns:
            PageAnalysis: 分析结果
        """
        try:
            self.logger.info(f"🔍 开始分析页面: {url}")
            
            # 导航到页面
            await self.browser_service.navigate_to_url(url)
            
            # 等待页面加载完成
            await asyncio.sleep(3)
            
            # 执行综合分析脚本
            analysis_script = """
            () => {
                const analysis = {
                    url: window.location.href,
                    title: document.title,
                    load_time: performance.timing.loadEventEnd - performance.timing.navigationStart,
                    elements_count: document.querySelectorAll('*').length,
                    network_requests: [],
                    product_elements: [],
                    anti_crawling_indicators: [],
                    performance_metrics: {}
                };
                
                // 性能指标
                if (performance.getEntriesByType) {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    if (navigation) {
                        analysis.performance_metrics = {
                            dns_lookup: navigation.domainLookupEnd - navigation.domainLookupStart,
                            tcp_connect: navigation.connectEnd - navigation.connectStart,
                            request_response: navigation.responseEnd - navigation.requestStart,
                            dom_loading: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                            page_load: navigation.loadEventEnd - navigation.loadEventStart
                        };
                    }
                }
                
                // 分析商品元素
                const productSelectors = [
                    '[data-spm*="product"]',
                    '[data-category="auctions"]',
                    '.recommend-item',
                    '.item',
                    '.product-item'
                ];
                
                productSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach((el, index) => {
                        if (index < 10) { // 限制数量避免过多数据
                            const rect = el.getBoundingClientRect();
                            analysis.product_elements.push({
                                tag_name: el.tagName.toLowerCase(),
                                selector: selector,
                                text_content: el.textContent.substring(0, 100),
                                attributes: {
                                    class: el.className,
                                    id: el.id,
                                    'data-spm': el.getAttribute('data-spm') || ''
                                },
                                position: {
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                }
                            });
                        }
                    });
                });
                
                // 检测反爬虫元素
                const antiCrawlingSelectors = [
                    '.captcha',
                    '#nc_1_n1z',
                    '.verify-code',
                    '.slider-verify',
                    '[class*="verify"]',
                    '[id*="captcha"]'
                ];
                
                antiCrawlingSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        analysis.anti_crawling_indicators.push({
                            selector: selector,
                            count: elements.length,
                            visible: Array.from(elements).some(el => 
                                el.offsetWidth > 0 && el.offsetHeight > 0
                            )
                        });
                    }
                });
                
                // 检测页面内容中的反爬虫关键词
                const pageText = document.body.textContent.toLowerCase();
                const antiCrawlingKeywords = [
                    '验证码', 'captcha', '请输入验证码', '访问过于频繁',
                    '请稍后再试', 'blocked', '403', '429'
                ];
                
                antiCrawlingKeywords.forEach(keyword => {
                    if (pageText.includes(keyword.toLowerCase())) {
                        analysis.anti_crawling_indicators.push({
                            type: 'text',
                            keyword: keyword,
                            found: true
                        });
                    }
                });
                
                return analysis;
            }
            """
            
            # 执行分析脚本
            if hasattr(self.browser_service.browser_driver, 'page') and self.browser_service.browser_driver.page:
                raw_analysis = await self.browser_service.browser_driver.page.evaluate(analysis_script)
                
                # 转换为 PageAnalysis 对象
                analysis = PageAnalysis(
                    url=raw_analysis.get('url', url),
                    title=raw_analysis.get('title', ''),
                    load_time=raw_analysis.get('load_time', 0) / 1000,  # 转换为秒
                    elements_count=raw_analysis.get('elements_count', 0),
                    network_requests=[],  # 需要额外的网络监控
                    product_elements=[
                        PageElement(
                            tag_name=elem.get('tag_name', ''),
                            selector=elem.get('selector', ''),
                            text_content=elem.get('text_content', ''),
                            attributes=elem.get('attributes', {}),
                            position=elem.get('position', {})
                        ) for elem in raw_analysis.get('product_elements', [])
                    ],
                    anti_crawling_indicators=raw_analysis.get('anti_crawling_indicators', []),
                    performance_metrics=raw_analysis.get('performance_metrics', {})
                )
                
                self.logger.info(f"✅ 页面分析完成: 发现 {len(analysis.product_elements)} 个商品元素")
                
                return analysis
            
            else:
                raise Exception("浏览器页面未初始化")
                
        except Exception as e:
            self.logger.error(f"❌ 页面分析失败: {e}")
            return PageAnalysis(
                url=url,
                title="",
                load_time=0,
                elements_count=0,
                network_requests=[],
                product_elements=[],
                anti_crawling_indicators=[],
                performance_metrics={}
            )
    
    async def monitor_network_requests(self, duration: int = 30) -> List[NetworkRequest]:
        """
        监控网络请求（模拟实现）
        
        Args:
            duration: 监控时长（秒）
            
        Returns:
            List[NetworkRequest]: 网络请求列表
        """
        try:
            self.logger.info(f"🌐 开始监控网络请求 ({duration} 秒)")
            
            # 在实际的 Chrome DevTools 集成中，这里会监听网络事件
            # 目前提供模拟实现
            
            monitoring_script = """
            () => {
                return new Promise((resolve) => {
                    const requests = [];
                    const originalFetch = window.fetch;
                    const originalXHROpen = XMLHttpRequest.prototype.open;
                    
                    // 拦截 fetch 请求
                    window.fetch = function(...args) {
                        const startTime = performance.now();
                        return originalFetch.apply(this, args).then(response => {
                            const endTime = performance.now();
                            requests.push({
                                url: args[0],
                                method: args[1]?.method || 'GET',
                                status: response.status,
                                response_type: 'fetch',
                                size: 0, // 无法直接获取
                                timing: {
                                    duration: endTime - startTime
                                },
                                headers: {}
                            });
                            return response;
                        });
                    };
                    
                    // 拦截 XMLHttpRequest
                    XMLHttpRequest.prototype.open = function(method, url) {
                        this._startTime = performance.now();
                        this._method = method;
                        this._url = url;
                        
                        this.addEventListener('loadend', () => {
                            const endTime = performance.now();
                            requests.push({
                                url: this._url,
                                method: this._method,
                                status: this.status,
                                response_type: 'xhr',
                                size: this.responseText ? this.responseText.length : 0,
                                timing: {
                                    duration: endTime - this._startTime
                                },
                                headers: {}
                            });
                        });
                        
                        return originalXHROpen.apply(this, arguments);
                    };
                    
                    // 设置定时器返回结果
                    setTimeout(() => {
                        resolve(requests);
                    }, """ + str(duration * 1000) + """);
                });
            }
            """
            
            if hasattr(self.browser_service.browser_driver, 'page') and self.browser_service.browser_driver.page:
                raw_requests = await self.browser_service.browser_driver.page.evaluate(monitoring_script)
                
                # 转换为 NetworkRequest 对象
                requests = [
                    NetworkRequest(
                        url=req.get('url', ''),
                        method=req.get('method', ''),
                        status=req.get('status', 0),
                        response_type=req.get('response_type', ''),
                        size=req.get('size', 0),
                        timing=req.get('timing', {}),
                        headers=req.get('headers', {})
                    ) for req in raw_requests
                ]
                
                self.logger.info(f"✅ 网络监控完成: 捕获 {len(requests)} 个请求")
                return requests
            
            return []
            
        except Exception as e:
            self.logger.error(f"❌ 网络监控失败: {e}")
            return []
    
    async def detect_anti_crawling_mechanisms(self) -> Dict[str, Any]:
        """
        检测反爬虫机制
        
        Returns:
            Dict[str, Any]: 检测结果
        """
        try:
            self.logger.info("🛡️ 检测反爬虫机制")
            
            detection_script = """
            () => {
                const detection = {
                    captcha_elements: [],
                    suspicious_scripts: [],
                    rate_limiting_indicators: [],
                    fingerprinting_attempts: [],
                    bot_detection_signals: []
                };
                
                // 检测验证码元素
                const captchaSelectors = [
                    '.captcha', '#nc_1_n1z', '.verify-code', '.slider-verify',
                    '[class*="verify"]', '[id*="captcha"]', '[class*="captcha"]'
                ];
                
                captchaSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        detection.captcha_elements.push({
                            selector: selector,
                            count: elements.length,
                            visible: Array.from(elements).some(el => 
                                el.offsetWidth > 0 && el.offsetHeight > 0
                            )
                        });
                    }
                });
                
                // 检测可疑脚本
                const scripts = document.querySelectorAll('script');
                scripts.forEach(script => {
                    const src = script.src;
                    const content = script.textContent;
                    
                    // 检测反爬虫相关的脚本特征
                    const suspiciousPatterns = [
                        'bot', 'crawler', 'spider', 'captcha', 'verify',
                        'fingerprint', 'detection', 'challenge'
                    ];
                    
                    suspiciousPatterns.forEach(pattern => {
                        if ((src && src.toLowerCase().includes(pattern)) ||
                            (content && content.toLowerCase().includes(pattern))) {
                            detection.suspicious_scripts.push({
                                type: src ? 'external' : 'inline',
                                source: src || 'inline',
                                pattern: pattern
                            });
                        }
                    });
                });
                
                // 检测限流指示器
                const pageText = document.body.textContent.toLowerCase();
                const rateLimitingKeywords = [
                    '访问过于频繁', '请稍后再试', 'too many requests',
                    'rate limit', '429', 'blocked'
                ];
                
                rateLimitingKeywords.forEach(keyword => {
                    if (pageText.includes(keyword)) {
                        detection.rate_limiting_indicators.push({
                            keyword: keyword,
                            found: true
                        });
                    }
                });
                
                // 检测指纹识别尝试
                if (window.navigator) {
                    const fingerprintingChecks = [
                        'webdriver' in window.navigator,
                        'plugins' in window.navigator && window.navigator.plugins.length === 0,
                        'languages' in window.navigator && window.navigator.languages.length === 0
                    ];
                    
                    fingerprintingChecks.forEach((check, index) => {
                        if (check) {
                            detection.fingerprinting_attempts.push({
                                type: ['webdriver', 'plugins', 'languages'][index],
                                detected: true
                            });
                        }
                    });
                }
                
                return detection;
            }
            """
            
            if hasattr(self.browser_service.browser_driver, 'page') and self.browser_service.browser_driver.page:
                detection_result = await self.browser_service.browser_driver.page.evaluate(detection_script)
                
                self.logger.info("✅ 反爬虫机制检测完成")
                return detection_result
            
            return {}
            
        except Exception as e:
            self.logger.error(f"❌ 反爬虫检测失败: {e}")
            return {}
    
    async def generate_analysis_report(self, analysis: PageAnalysis, 
                                     network_requests: List[NetworkRequest],
                                     anti_crawling_detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成综合分析报告
        
        Args:
            analysis: 页面分析结果
            network_requests: 网络请求列表
            anti_crawling_detection: 反爬虫检测结果
            
        Returns:
            Dict[str, Any]: 综合报告
        """
        report = {
            'analysis_timestamp': asyncio.get_event_loop().time(),
            'page_info': {
                'url': analysis.url,
                'title': analysis.title,
                'load_time': analysis.load_time,
                'elements_count': analysis.elements_count
            },
            'performance_metrics': analysis.performance_metrics,
            'product_analysis': {
                'total_product_elements': len(analysis.product_elements),
                'selectors_effectiveness': self._analyze_selector_effectiveness(analysis.product_elements),
                'element_distribution': self._analyze_element_distribution(analysis.product_elements)
            },
            'network_analysis': {
                'total_requests': len(network_requests),
                'request_types': self._analyze_request_types(network_requests),
                'performance_summary': self._analyze_network_performance(network_requests)
            },
            'anti_crawling_assessment': {
                'risk_level': self._assess_anti_crawling_risk(anti_crawling_detection),
                'detected_mechanisms': anti_crawling_detection,
                'recommendations': self._generate_recommendations(anti_crawling_detection)
            }
        }
        
        return report
    
    def _analyze_selector_effectiveness(self, elements: List[PageElement]) -> Dict[str, int]:
        """分析选择器有效性"""
        selector_counts = {}
        for element in elements:
            selector = element.selector
            selector_counts[selector] = selector_counts.get(selector, 0) + 1
        return selector_counts
    
    def _analyze_element_distribution(self, elements: List[PageElement]) -> Dict[str, Any]:
        """分析元素分布"""
        if not elements:
            return {}
        
        positions = [elem.position for elem in elements if elem.position]
        if not positions:
            return {}
        
        return {
            'avg_x': sum(pos.get('x', 0) for pos in positions) / len(positions),
            'avg_y': sum(pos.get('y', 0) for pos in positions) / len(positions),
            'avg_width': sum(pos.get('width', 0) for pos in positions) / len(positions),
            'avg_height': sum(pos.get('height', 0) for pos in positions) / len(positions)
        }
    
    def _analyze_request_types(self, requests: List[NetworkRequest]) -> Dict[str, int]:
        """分析请求类型"""
        types = {}
        for request in requests:
            req_type = request.response_type
            types[req_type] = types.get(req_type, 0) + 1
        return types
    
    def _analyze_network_performance(self, requests: List[NetworkRequest]) -> Dict[str, float]:
        """分析网络性能"""
        if not requests:
            return {}
        
        durations = [req.timing.get('duration', 0) for req in requests if req.timing]
        if not durations:
            return {}
        
        return {
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'min_duration': min(durations),
            'total_requests': len(requests)
        }
    
    def _assess_anti_crawling_risk(self, detection: Dict[str, Any]) -> str:
        """评估反爬虫风险等级"""
        risk_score = 0
        
        # 验证码元素
        if detection.get('captcha_elements'):
            risk_score += 3
        
        # 可疑脚本
        if detection.get('suspicious_scripts'):
            risk_score += 2
        
        # 限流指示器
        if detection.get('rate_limiting_indicators'):
            risk_score += 4
        
        # 指纹识别
        if detection.get('fingerprinting_attempts'):
            risk_score += 2
        
        if risk_score >= 6:
            return "HIGH"
        elif risk_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(self, detection: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if detection.get('captcha_elements'):
            recommendations.append("检测到验证码元素，建议降低请求频率并使用真实浏览器环境")
        
        if detection.get('rate_limiting_indicators'):
            recommendations.append("检测到限流机制，建议增加请求间隔时间")
        
        if detection.get('fingerprinting_attempts'):
            recommendations.append("检测到指纹识别，建议使用真实用户代理和浏览器配置")
        
        if not recommendations:
            recommendations.append("未检测到明显的反爬虫机制，可以正常进行数据抓取")
        
        return recommendations

# 使用示例
async def analyze_taobao_page():
    """分析淘宝页面的示例"""
    from ..rpa.browser.browser_service import BrowserService
    from ..rpa.browser.core.models.browser_config import BrowserConfig, BrowserType
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建浏览器服务
    config = BrowserConfig(
        browser_type=BrowserType.CHROME,
        headless=True,
        viewport={'width': 1920, 'height': 1080}
    )
    
    browser_service = BrowserService(config=config, debug_mode=True)
    
    try:
        # 初始化浏览器
        await browser_service.initialize()
        
        # 创建分析器
        analyzer = ChromeDevToolsAnalyzer(browser_service)
        
        # 分析淘宝搜索页面
        url = "https://s.taobao.com/search?q=iPhone"
        
        print("🔍 开始分析淘宝页面...")
        
        # 页面分析
        analysis = await analyzer.analyze_page(url)
        
        # 网络监控
        network_requests = await analyzer.monitor_network_requests(10)
        
        # 反爬虫检测
        anti_crawling = await analyzer.detect_anti_crawling_mechanisms()
        
        # 生成报告
        report = await analyzer.generate_analysis_report(
            analysis, network_requests, anti_crawling
        )
        
        # 输出结果
        print(f"\n📊 分析报告:")
        print(f"   页面标题: {analysis.title}")
        print(f"   加载时间: {analysis.load_time:.2f} 秒")
        print(f"   商品元素: {len(analysis.product_elements)} 个")
        print(f"   网络请求: {len(network_requests)} 个")
        print(f"   反爬虫风险: {report['anti_crawling_assessment']['risk_level']}")
        
        # 保存报告
        with open('taobao_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细报告已保存到: taobao_analysis_report.json")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
    
    finally:
        await browser_service.close()

if __name__ == "__main__":
    asyncio.run(analyze_taobao_page())