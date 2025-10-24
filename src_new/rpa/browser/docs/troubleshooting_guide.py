"""
Troubleshooting Guide and FAQ
=============================

This document provides comprehensive troubleshooting guidance and frequently asked questions
for the browser automation system migration and usage.

Table of Contents
-----------------
1. Common Migration Issues
2. Runtime Error Solutions
3. Performance Issues
4. Configuration Problems
5. Browser Compatibility Issues
6. Network and Timeout Issues
7. Element Detection Problems
8. Memory and Resource Issues
9. Debugging Tools and Techniques
10. Frequently Asked Questions
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from src_new.rpa.browser.core.browser_service import BrowserService
from src_new.rpa.browser.config.config_manager import ConfigManager
from src_new.rpa.browser.exceptions import BrowserError, NavigationError, TimeoutError


# ============================================================================
# 1. Common Migration Issues
# ============================================================================

class MigrationTroubleshooter:
    """Migration troubleshooting utilities"""
    
    @staticmethod
    async def diagnose_import_errors():
        """Diagnose common import errors during migration"""
        
        issues = []
        
        try:
            from src_new.rpa.browser.core.browser_service import BrowserService
        except ImportError as e:
            issues.append({
                'type': 'import_error',
                'module': 'BrowserService',
                'error': str(e),
                'solution': 'Ensure src_new/rpa/browser is in Python path and all dependencies are installed'
            })
        
        try:
            import playwright
        except ImportError as e:
            issues.append({
                'type': 'dependency_error',
                'module': 'playwright',
                'error': str(e),
                'solution': 'Install playwright: pip install playwright && playwright install'
            })
        
        try:
            import yaml
        except ImportError as e:
            issues.append({
                'type': 'dependency_error',
                'module': 'yaml',
                'error': str(e),
                'solution': 'Install PyYAML: pip install PyYAML'
            })
        
        return issues
    
    @staticmethod
    async def validate_config_migration(old_config_path: str, new_config_path: str):
        """Validate configuration migration"""
        
        validation_results = {
            'old_config_exists': False,
            'new_config_exists': False,
            'config_valid': False,
            'missing_fields': [],
            'recommendations': []
        }
        
        # Check old config exists
        import os
        if os.path.exists(old_config_path):
            validation_results['old_config_exists'] = True
        else:
            validation_results['recommendations'].append(f"Old config not found at {old_config_path}")
        
        # Check new config exists
        if os.path.exists(new_config_path):
            validation_results['new_config_exists'] = True
            
            try:
                config_manager = ConfigManager()
                await config_manager.load_config(new_config_path)
                validation_results['config_valid'] = True
                
                # Check required fields
                required_fields = [
                    'browser.headless',
                    'browser.timeout',
                    'browser.viewport',
                    'logging.level'
                ]
                
                for field in required_fields:
                    if not config_manager.get(field):
                        validation_results['missing_fields'].append(field)
                
            except Exception as e:
                validation_results['config_valid'] = False
                validation_results['recommendations'].append(f"Config validation failed: {e}")
        
        return validation_results
    
    @staticmethod
    def generate_migration_report(old_code_path: str, new_code_path: str):
        """Generate migration compatibility report"""
        
        report = {
            'compatibility_score': 0.0,
            'issues': [],
            'recommendations': [],
            'migration_steps': []
        }
        
        # Check for common migration patterns
        migration_patterns = [
            {
                'old_pattern': 'from playwright.sync_api import sync_playwright',
                'new_pattern': 'from src_new.rpa.browser.core.browser_service import BrowserService',
                'description': 'Replace direct Playwright usage with BrowserService'
            },
            {
                'old_pattern': 'browser = p.chromium.launch()',
                'new_pattern': 'browser_service = BrowserService(config_manager)',
                'description': 'Use BrowserService instead of direct browser launch'
            },
            {
                'old_pattern': 'page.goto(url)',
                'new_pattern': 'await browser_service.navigate_to(url)',
                'description': 'Use async navigation methods'
            }
        ]
        
        report['migration_steps'] = migration_patterns
        report['compatibility_score'] = 0.85  # Estimated based on patterns
        
        return report


# ============================================================================
# 2. Runtime Error Solutions
# ============================================================================

class RuntimeErrorSolver:
    """Runtime error diagnosis and solutions"""
    
    @staticmethod
    async def diagnose_browser_launch_failure():
        """Diagnose browser launch failures"""
        
        solutions = []
        
        try:
            # Test basic browser launch
            config_manager = ConfigManager()
            await config_manager.load_from_dict({
                'browser': {
                    'headless': True,
                    'timeout': 30000
                }
            })
            
            browser_service = BrowserService(config_manager)
            await browser_service.initialize()
            await browser_service.cleanup()
            
            solutions.append({
                'status': 'success',
                'message': 'Browser launch test successful'
            })
            
        except Exception as e:
            error_type = type(e).__name__
            
            if 'Executable doesn\'t exist' in str(e):
                solutions.append({
                    'status': 'error',
                    'error_type': 'missing_browser',
                    'message': 'Browser executable not found',
                    'solution': 'Run: playwright install chromium'
                })
            
            elif 'Permission denied' in str(e):
                solutions.append({
                    'status': 'error',
                    'error_type': 'permission_error',
                    'message': 'Permission denied accessing browser',
                    'solution': 'Check file permissions or run with appropriate privileges'
                })
            
            elif 'timeout' in str(e).lower():
                solutions.append({
                    'status': 'error',
                    'error_type': 'timeout_error',
                    'message': 'Browser launch timeout',
                    'solution': 'Increase timeout or check system resources'
                })
            
            else:
                solutions.append({
                    'status': 'error',
                    'error_type': error_type,
                    'message': str(e),
                    'solution': 'Check logs and system requirements'
                })
        
        return solutions
    
    @staticmethod
    async def diagnose_navigation_issues(url: str):
        """Diagnose navigation issues"""
        
        issues = []
        
        # URL validation
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            issues.append({
                'type': 'invalid_url',
                'message': f'Invalid URL format: {url}',
                'solution': 'Ensure URL includes protocol (http:// or https://)'
            })
        
        # Network connectivity test
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=10)
            issues.append({
                'type': 'connectivity',
                'message': 'URL is accessible',
                'status': 'success'
            })
        except Exception as e:
            issues.append({
                'type': 'connectivity_error',
                'message': f'Cannot access URL: {e}',
                'solution': 'Check network connection and URL availability'
            })
        
        return issues
    
    @staticmethod
    async def diagnose_element_detection_issues():
        """Diagnose element detection problems"""
        
        common_issues = [
            {
                'issue': 'Element not found',
                'causes': [
                    'Element not loaded yet',
                    'Incorrect selector',
                    'Element in iframe',
                    'Dynamic content not rendered'
                ],
                'solutions': [
                    'Increase wait timeout',
                    'Use wait_for_element() method',
                    'Verify selector with browser dev tools',
                    'Check for iframe context',
                    'Wait for network idle state'
                ]
            },
            {
                'issue': 'Element not clickable',
                'causes': [
                    'Element covered by another element',
                    'Element not visible',
                    'Element disabled',
                    'Page still loading'
                ],
                'solutions': [
                    'Scroll element into view',
                    'Wait for element to be visible',
                    'Check element state',
                    'Use force_click if necessary'
                ]
            },
            {
                'issue': 'Stale element reference',
                'causes': [
                    'Page refreshed after element found',
                    'DOM modified by JavaScript',
                    'Navigation occurred'
                ],
                'solutions': [
                    'Re-find element before use',
                    'Use fresh selectors',
                    'Implement retry logic'
                ]
            }
        ]
        
        return common_issues


# ============================================================================
# 3. Performance Issues
# ============================================================================

class PerformanceDiagnostic:
    """Performance issue diagnosis and optimization"""
    
    @staticmethod
    async def analyze_page_load_performance(url: str):
        """Analyze page load performance"""
        
        import time
        
        performance_metrics = {
            'url': url,
            'load_times': {},
            'resource_counts': {},
            'recommendations': []
        }
        
        try:
            config_manager = ConfigManager()
            await config_manager.load_from_dict({
                'browser': {
                    'headless': True,
                    'timeout': 30000
                }
            })
            
            browser_service = BrowserService(config_manager)
            await browser_service.initialize()
            
            # Measure navigation time
            start_time = time.time()
            await browser_service.navigate_to(url)
            navigation_time = time.time() - start_time
            
            # Measure load state times
            start_time = time.time()
            await browser_service.wait_for_load_state('domcontentloaded')
            dom_load_time = time.time() - start_time
            
            start_time = time.time()
            await browser_service.wait_for_load_state('networkidle')
            network_idle_time = time.time() - start_time
            
            performance_metrics['load_times'] = {
                'navigation': navigation_time,
                'dom_content_loaded': dom_load_time,
                'network_idle': network_idle_time,
                'total': navigation_time + dom_load_time + network_idle_time
            }
            
            # Performance recommendations
            if performance_metrics['load_times']['total'] > 10:
                performance_metrics['recommendations'].append(
                    'Consider enabling resource filtering to improve load times'
                )
            
            if performance_metrics['load_times']['network_idle'] > 5:
                performance_metrics['recommendations'].append(
                    'Long network idle time detected, consider using domcontentloaded instead'
                )
            
            await browser_service.cleanup()
            
        except Exception as e:
            performance_metrics['error'] = str(e)
            performance_metrics['recommendations'].append(
                'Performance analysis failed, check URL accessibility'
            )
        
        return performance_metrics
    
    @staticmethod
    def get_memory_optimization_tips():
        """Get memory optimization recommendations"""
        
        tips = [
            {
                'category': 'Browser Configuration',
                'tips': [
                    'Use headless mode in production',
                    'Disable images if not needed: disable_images: true',
                    'Limit viewport size: viewport: {width: 1280, height: 720}',
                    'Set reasonable timeouts'
                ]
            },
            {
                'category': 'Resource Management',
                'tips': [
                    'Always call cleanup() in finally blocks',
                    'Use context managers when possible',
                    'Limit concurrent browser instances',
                    'Close unused tabs promptly'
                ]
            },
            {
                'category': 'Data Processing',
                'tips': [
                    'Process data in batches',
                    'Use generators for large datasets',
                    'Clear data structures when done',
                    'Implement pagination limits'
                ]
            }
        ]
        
        return tips


# ============================================================================
# 4. Configuration Problems
# ============================================================================

class ConfigurationValidator:
    """Configuration validation and fixing"""
    
    @staticmethod
    async def validate_configuration(config_path: str):
        """Comprehensive configuration validation"""
        
        validation_report = {
            'config_path': config_path,
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            config_manager = ConfigManager()
            await config_manager.load_config(config_path)
            
            # Validate required sections
            required_sections = ['browser', 'logging']
            for section in required_sections:
                if not config_manager.get(section):
                    validation_report['errors'].append(f'Missing required section: {section}')
            
            # Validate browser configuration
            browser_config = config_manager.get('browser', {})
            
            # Check timeout values
            timeout = browser_config.get('timeout', 30000)
            if timeout < 5000:
                validation_report['warnings'].append('Timeout too low, may cause failures')
            elif timeout > 120000:
                validation_report['warnings'].append('Timeout very high, may slow down execution')
            
            # Check viewport configuration
            viewport = browser_config.get('viewport', {})
            if viewport:
                width = viewport.get('width', 1920)
                height = viewport.get('height', 1080)
                
                if width < 800 or height < 600:
                    validation_report['warnings'].append('Viewport size too small, may affect element detection')
            
            # Validate logging configuration
            logging_config = config_manager.get('logging', {})
            log_level = logging_config.get('level', 'INFO')
            
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if log_level not in valid_levels:
                validation_report['errors'].append(f'Invalid log level: {log_level}')
            
            # Check for performance optimizations
            if not browser_config.get('headless', False):
                validation_report['suggestions'].append('Consider using headless mode for better performance')
            
            if not browser_config.get('disable_images', False):
                validation_report['suggestions'].append('Consider disabling images if not needed')
            
            validation_report['is_valid'] = len(validation_report['errors']) == 0
            
        except Exception as e:
            validation_report['errors'].append(f'Configuration loading failed: {e}')
        
        return validation_report
    
    @staticmethod
    def generate_sample_config():
        """Generate a sample configuration file"""
        
        sample_config = {
            'browser': {
                'headless': True,
                'timeout': 30000,
                'viewport': {
                    'width': 1920,
                    'height': 1080
                },
                'user_agent': 'Mozilla/5.0 (compatible; AutomationBot/1.0)',
                'disable_images': False,
                'disable_javascript': False
            },
            'dom_analysis': {
                'max_depth': 10,
                'extract_text': True,
                'extract_links': True,
                'extract_images': True,
                'timeout': 5000
            },
            'pagination': {
                'max_pages': 100,
                'delay_between_pages': 1.0,
                'pagination_types': ['numeric', 'scroll', 'load_more'],
                'scroll_pause_time': 2.0
            },
            'logging': {
                'level': 'INFO',
                'format': 'structured',
                'output_file': 'logs/browser_automation.log',
                'max_file_size': '10MB',
                'backup_count': 5,
                'console_output': True
            },
            'performance': {
                'concurrent_limit': 3,
                'retry_attempts': 3,
                'retry_delay': 1.0,
                'cache_enabled': True
            }
        }
        
        return sample_config


# ============================================================================
# 5. Browser Compatibility Issues
# ============================================================================

class BrowserCompatibilityChecker:
    """Browser compatibility diagnosis"""
    
    @staticmethod
    async def check_browser_support():
        """Check browser installation and support"""
        
        compatibility_report = {
            'browsers': {},
            'recommendations': []
        }
        
        browsers_to_check = ['chromium', 'firefox', 'webkit']
        
        for browser_name in browsers_to_check:
            try:
                config_manager = ConfigManager()
                await config_manager.load_from_dict({
                    'browser': {
                        'browser_type': browser_name,
                        'headless': True,
                        'timeout': 10000
                    }
                })
                
                browser_service = BrowserService(config_manager)
                await browser_service.initialize()
                await browser_service.cleanup()
                
                compatibility_report['browsers'][browser_name] = {
                    'available': True,
                    'status': 'working'
                }
                
            except Exception as e:
                compatibility_report['browsers'][browser_name] = {
                    'available': False,
                    'status': 'failed',
                    'error': str(e)
                }
        
        # Generate recommendations
        working_browsers = [name for name, info in compatibility_report['browsers'].items() 
                          if info.get('available', False)]
        
        if not working_browsers:
            compatibility_report['recommendations'].append(
                'No browsers available. Run: playwright install'
            )
        elif len(working_browsers) == 1:
            compatibility_report['recommendations'].append(
                f'Only {working_browsers[0]} available. Consider installing other browsers for testing'
            )
        
        return compatibility_report
    
    @staticmethod
    def get_browser_specific_solutions():
        """Get browser-specific issue solutions"""
        
        solutions = {
            'chromium': {
                'common_issues': [
                    {
                        'issue': 'Chrome crashes on startup',
                        'solutions': [
                            'Add --no-sandbox flag in headless mode',
                            'Increase shared memory: --shm-size=2g',
                            'Disable dev-shm usage: --disable-dev-shm-usage'
                        ]
                    },
                    {
                        'issue': 'Permission denied errors',
                        'solutions': [
                            'Run with --no-sandbox flag',
                            'Check file permissions',
                            'Use proper user context'
                        ]
                    }
                ]
            },
            'firefox': {
                'common_issues': [
                    {
                        'issue': 'Firefox fails to start',
                        'solutions': [
                            'Check Firefox installation',
                            'Update Firefox version',
                            'Clear Firefox profile'
                        ]
                    }
                ]
            },
            'webkit': {
                'common_issues': [
                    {
                        'issue': 'WebKit not available on Linux',
                        'solutions': [
                            'WebKit only supported on macOS and Windows',
                            'Use Chromium or Firefox on Linux',
                            'Consider Docker with macOS/Windows base'
                        ]
                    }
                ]
            }
        }
        
        return solutions


# ============================================================================
# 6. Network and Timeout Issues
# ============================================================================

class NetworkDiagnostic:
    """Network and timeout issue diagnosis"""
    
    @staticmethod
    async def diagnose_timeout_issues():
        """Diagnose various timeout scenarios"""
        
        timeout_scenarios = [
            {
                'scenario': 'Page Load Timeout',
                'causes': [
                    'Slow server response',
                    'Large page size',
                    'Network connectivity issues',
                    'Timeout value too low'
                ],
                'solutions': [
                    'Increase page timeout',
                    'Use wait_for_load_state("domcontentloaded")',
                    'Check network connectivity',
                    'Implement retry logic'
                ]
            },
            {
                'scenario': 'Element Wait Timeout',
                'causes': [
                    'Element never appears',
                    'Incorrect selector',
                    'Element in different frame',
                    'JavaScript not executed'
                ],
                'solutions': [
                    'Verify element selector',
                    'Increase element wait timeout',
                    'Check for iframe context',
                    'Wait for JavaScript execution'
                ]
            },
            {
                'scenario': 'Network Request Timeout',
                'causes': [
                    'Slow API responses',
                    'Network latency',
                    'Server overload',
                    'Firewall blocking'
                ],
                'solutions': [
                    'Increase network timeout',
                    'Implement request retry',
                    'Check server status',
                    'Verify network configuration'
                ]
            }
        ]
        
        return timeout_scenarios
    
    @staticmethod
    async def test_network_connectivity(urls: List[str]):
        """Test network connectivity to multiple URLs"""
        
        connectivity_results = []
        
        for url in urls:
            result = {
                'url': url,
                'accessible': False,
                'response_time': None,
                'error': None
            }
            
            try:
                import time
                import urllib.request
                
                start_time = time.time()
                response = urllib.request.urlopen(url, timeout=10)
                response_time = time.time() - start_time
                
                result['accessible'] = True
                result['response_time'] = response_time
                result['status_code'] = response.getcode()
                
            except Exception as e:
                result['error'] = str(e)
            
            connectivity_results.append(result)
        
        return connectivity_results


# ============================================================================
# 7. Debugging Tools and Techniques
# ============================================================================

class DebuggingToolkit:
    """Debugging utilities and techniques"""
    
    @staticmethod
    async def enable_debug_mode(config_manager: ConfigManager):
        """Enable comprehensive debug mode"""
        
        debug_config = {
            'browser': {
                'headless': False,  # Show browser for debugging
                'devtools': True,   # Open dev tools
                'slow_mo': 100      # Slow down actions
            },
            'logging': {
                'level': 'DEBUG',
                'console_output': True,
                'detailed_errors': True
            }
        }
        
        await config_manager.load_from_dict(debug_config, merge=True)
        
        return debug_config
    
    @staticmethod
    async def capture_debug_info(browser_service: BrowserService, error_context: str):
        """Capture comprehensive debug information"""
        
        debug_info = {
            'timestamp': time.time(),
            'context': error_context,
            'page_info': {},
            'browser_info': {},
            'screenshots': []
        }
        
        try:
            # Capture page information
            debug_info['page_info'] = {
                'url': await browser_service.get_current_url(),
                'title': await browser_service.get_page_title(),
                'ready_state': await browser_service.get_ready_state()
            }
            
            # Take screenshot
            screenshot_path = f'debug_screenshot_{int(time.time())}.png'
            await browser_service.take_screenshot(screenshot_path)
            debug_info['screenshots'].append(screenshot_path)
            
            # Capture console logs
            console_logs = await browser_service.get_console_logs()
            debug_info['console_logs'] = console_logs
            
        except Exception as e:
            debug_info['capture_error'] = str(e)
        
        return debug_info
    
    @staticmethod
    def generate_debug_report(debug_sessions: List[Dict]):
        """Generate comprehensive debug report"""
        
        report = {
            'summary': {
                'total_sessions': len(debug_sessions),
                'failed_sessions': 0,
                'common_errors': {},
                'performance_stats': {}
            },
            'sessions': debug_sessions,
            'recommendations': []
        }
        
        # Analyze sessions
        error_counts = {}
        for session in debug_sessions:
            if 'error' in session:
                error_type = type(session['error']).__name__
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                report['summary']['failed_sessions'] += 1
        
        report['summary']['common_errors'] = error_counts
        
        # Generate recommendations
        if error_counts.get('TimeoutError', 0) > 0:
            report['recommendations'].append('Consider increasing timeout values')
        
        if error_counts.get('NavigationError', 0) > 0:
            report['recommendations'].append('Check URL accessibility and network connectivity')
        
        return report


# ============================================================================
# 8. Frequently Asked Questions
# ============================================================================

class FAQ:
    """Frequently Asked Questions and Solutions"""
    
    @staticmethod
    def get_migration_faq():
        """Get migration-related FAQ"""
        
        faq_items = [
            {
                'question': 'How do I migrate from sync to async code?',
                'answer': '''
                Replace synchronous calls with async/await:
                
                Old (sync):
                ```python
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page()
                    page.goto(url)
                ```
                
                New (async):
                ```python
                browser_service = BrowserService(config_manager)
                await browser_service.initialize()
                await browser_service.navigate_to(url)
                ```
                '''
            },
            {
                'question': 'Can I use the old and new systems simultaneously?',
                'answer': '''
                Yes, during migration you can run both systems in parallel:
                
                ```python
                # Run both systems for comparison
                old_result = run_old_system()
                new_result = await run_new_system()
                
                # Compare results and gradually switch
                if validate_results(old_result, new_result):
                    return new_result
                else:
                    return old_result
                ```
                '''
            },
            {
                'question': 'How do I handle custom Playwright code?',
                'answer': '''
                Extend the base classes:
                
                ```python
                class CustomBrowserService(BrowserService):
                    async def custom_action(self):
                        # Your custom logic here
                        pass
                ```
                '''
            },
            {
                'question': 'What about performance differences?',
                'answer': '''
                The new system is generally faster due to:
                - Better resource management
                - Optimized waiting strategies
                - Reduced overhead
                
                Use performance monitoring to compare:
                ```python
                await performance_test()
                ```
                '''
            }
        ]
        
        return faq_items
    
    @staticmethod
    def get_usage_faq():
        """Get usage-related FAQ"""
        
        faq_items = [
            {
                'question': 'How do I handle dynamic content?',
                'answer': '''
                Use appropriate waiting strategies:
                
                ```python
                # Wait for element
                await browser_service.wait_for_element('.dynamic-content')
                
                # Wait for text
                await browser_service.wait_for_text('Loading complete')
                
                # Wait for network idle
                await browser_service.wait_for_load_state('networkidle')
                ```
                '''
            },
            {
                'question': 'How do I handle multiple pages/tabs?',
                'answer': '''
                Use tab management methods:
                
                ```python
                # Open new tab
                await browser_service.new_tab(url)
                
                # Switch between tabs
                await browser_service.switch_to_tab(1)
                
                # Close tab
                await browser_service.close_tab(1)
                ```
                '''
            },
            {
                'question': 'How do I optimize for speed?',
                'answer': '''
                Use performance optimizations:
                
                ```python
                config = {
                    'browser': {
                        'headless': True,
                        'disable_images': True,
                        'disable_css': True  # if styling not needed
                    }
                }
                ```
                '''
            },
            {
                'question': 'How do I debug issues?',
                'answer': '''
                Enable debug mode:
                
                ```python
                config = {
                    'browser': {
                        'headless': False,
                        'devtools': True,
                        'slow_mo': 100
                    },
                    'logging': {
                        'level': 'DEBUG'
                    }
                }
                ```
                '''
            }
        ]
        
        return faq_items
    
    @staticmethod
    def get_troubleshooting_faq():
        """Get troubleshooting-related FAQ"""
        
        faq_items = [
            {
                'question': 'Browser fails to launch, what should I do?',
                'answer': '''
                1. Check browser installation: `playwright install`
                2. Verify permissions
                3. Try headless mode
                4. Check system resources
                5. Review error logs
                '''
            },
            {
                'question': 'Elements not found, how to fix?',
                'answer': '''
                1. Verify selector with browser dev tools
                2. Increase wait timeout
                3. Check for iframe context
                4. Wait for page load completion
                5. Use multiple selector strategies
                '''
            },
            {
                'question': 'Memory usage too high, how to optimize?',
                'answer': '''
                1. Use headless mode
                2. Disable unnecessary resources
                3. Limit concurrent instances
                4. Implement proper cleanup
                5. Process data in batches
                '''
            },
            {
                'question': 'Network timeouts, how to handle?',
                'answer': '''
                1. Increase timeout values
                2. Implement retry logic
                3. Check network connectivity
                4. Use exponential backoff
                5. Monitor server response times
                '''
            }
        ]
        
        return faq_items


# ============================================================================
# Utility Functions
# ============================================================================

async def run_comprehensive_diagnosis():
    """Run comprehensive system diagnosis"""
    
    diagnosis_report = {
        'timestamp': time.time(),
        'system_info': {},
        'import_check': {},
        'browser_check': {},
        'network_check': {},
        'recommendations': []
    }
    
    # Check imports
    migration_troubleshooter = MigrationTroubleshooter()
    diagnosis_report['import_check'] = await migration_troubleshooter.diagnose_import_errors()
    
    # Check browser compatibility
    browser_checker = BrowserCompatibilityChecker()
    diagnosis_report['browser_check'] = await browser_checker.check_browser_support()
    
    # Check network connectivity
    network_diagnostic = NetworkDiagnostic()
    test_urls = ['https://google.com', 'https://github.com', 'https://example.com']
    diagnosis_report['network_check'] = await network_diagnostic.test_network_connectivity(test_urls)
    
    # Generate recommendations
    if diagnosis_report['import_check']:
        diagnosis_report['recommendations'].append('Fix import errors before proceeding')
    
    working_browsers = [name for name, info in diagnosis_report['browser_check']['browsers'].items() 
                       if info.get('available', False)]
    if not working_browsers:
        diagnosis_report['recommendations'].append('Install browsers: playwright install')
    
    accessible_urls = [result for result in diagnosis_report['network_check'] 
                      if result.get('accessible', False)]
    if len(accessible_urls) < len(test_urls):
        diagnosis_report['recommendations'].append('Check network connectivity')
    
    return diagnosis_report


async def generate_troubleshooting_checklist():
    """Generate troubleshooting checklist"""
    
    checklist = {
        'pre_migration': [
            '□ Backup existing code and configuration',
            '□ Install required dependencies (playwright, PyYAML, etc.)',
            '□ Run browser installation: playwright install',
            '□ Test basic browser functionality',
            '□ Prepare test environment'
        ],
        'during_migration': [
            '□ Update import statements',
            '□ Convert sync code to async',
            '□ Update configuration format',
            '□ Test each migrated component',
            '□ Validate functionality equivalence'
        ],
        'post_migration': [
            '□ Run comprehensive tests',
            '□ Monitor performance metrics',
            '□ Check error logs',
            '□ Validate all use cases',
            '□ Update documentation'
        ],
        'troubleshooting': [
            '□ Check system requirements',
            '□ Verify browser installation',
            '□ Test network connectivity',
            '□ Review configuration files',
            '□ Enable debug logging',
            '□ Capture screenshots and logs',
            '□ Compare with working examples'
        ]
    }
    
    return checklist


if __name__ == "__main__":
    # Run diagnosis
    print("Running comprehensive system diagnosis...")
    diagnosis = asyncio.run(run_comprehensive_diagnosis())
    
    print("\nDiagnosis Results:")
    for key, value in diagnosis.items():
        if key != 'timestamp':
            print(f"{key}: {value}")
    
    # Generate checklist
    print("\nGenerating troubleshooting checklist...")
    checklist = asyncio.run(generate_troubleshooting_checklist())
    
    for category, items in checklist.items():
        print(f"\n{category.upper()}:")
        for item in items:
            print(f"  {item}")