#!/usr/bin/env python3
"""
跟卖检测多语言支持测试

测试不同语言环境下的跟卖检测功能
"""

import unittest
import logging
from unittest.mock import Mock, MagicMock
from bs4 import BeautifulSoup

from common.services.competitor_detection_service import CompetitorDetectionService
from common.models.scraping_result import CompetitorInfo, CompetitorDetectionResult
from common.config.ozon_selectors_config import OzonSelectorsConfig
from common.config.language_config import LanguageConfig, SupportedLanguage, get_language_config


class TestCompetitorMultilanguage(unittest.TestCase):
    """跟卖检测多语言支持测试类"""

    def setUp(self):
        """测试初始化"""
        self.logger = logging.getLogger(__name__)
        self.selectors_config = OzonSelectorsConfig()
        self.service = CompetitorDetectionService(
            selectors_config=self.selectors_config,
            logger=self.logger
        )
        self.language_config = get_language_config()

    def test_competitor_keywords_in_different_languages(self):
        """测试不同语言的跟卖关键词"""
        # 测试俄语关键词
        ru_keywords = self.language_config.get_competitor_keywords(SupportedLanguage.RUSSIAN)
        self.assertIsInstance(ru_keywords, list)
        self.assertGreater(len(ru_keywords), 0)
        
        # 测试中文关键词
        zh_keywords = self.language_config.get_competitor_keywords(SupportedLanguage.CHINESE)
        self.assertIsInstance(zh_keywords, list)
        
        # 测试英语关键词
        en_keywords = self.language_config.get_competitor_keywords(SupportedLanguage.ENGLISH)
        self.assertIsInstance(en_keywords, list)

    def test_competitor_count_patterns_in_different_languages(self):
        """测试不同语言的跟卖数量解析模式"""
        # 测试俄语模式
        ru_patterns = self.language_config.get_competitor_count_patterns(SupportedLanguage.RUSSIAN)
        self.assertIsInstance(ru_patterns, list)
        
        # 测试中文模式
        zh_patterns = self.language_config.get_competitor_count_patterns(SupportedLanguage.CHINESE)
        self.assertIsInstance(zh_patterns, list)
        
        # 测试英语模式
        en_patterns = self.language_config.get_competitor_count_patterns(SupportedLanguage.ENGLISH)
        self.assertIsInstance(en_patterns, list)

    def test_expand_button_texts_in_different_languages(self):
        """测试不同语言的展开按钮文本"""
        # 测试俄语文本
        ru_texts = self.language_config.get_expand_button_texts(SupportedLanguage.RUSSIAN)
        self.assertIsInstance(ru_texts, list)
        
        # 测试中文文本
        zh_texts = self.language_config.get_expand_button_texts(SupportedLanguage.CHINESE)
        self.assertIsInstance(zh_texts, list)
        
        # 测试英语文本
        en_texts = self.language_config.get_expand_button_texts(SupportedLanguage.ENGLISH)
        self.assertIsInstance(en_texts, list)

    def test_language_detection_from_text(self):
        """测试从文本中检测语言"""
        # 测试俄语文本
        ru_text = "Продают другие продавцы"
        detected_lang = self.language_config.detect_language_from_text(ru_text)
        self.assertEqual(detected_lang, SupportedLanguage.RUSSIAN)
        
        # 测试中文文本
        zh_text = "有其他卖家销售"
        detected_lang = self.language_config.detect_language_from_text(zh_text)
        self.assertEqual(detected_lang, SupportedLanguage.CHINESE)
        
        # 测试英语文本
        en_text = "Other sellers"
        detected_lang = self.language_config.detect_language_from_text(en_text)
        self.assertEqual(detected_lang, SupportedLanguage.ENGLISH)

    def test_set_language_from_environment(self):
        """测试从环境变量设置语言"""
        import os
        
        # 保存原始环境变量
        original_lang = os.environ.get('OZON_SCRAPER_LANGUAGE')
        
        try:
            # 设置俄语环境变量
            os.environ['OZON_SCRAPER_LANGUAGE'] = 'ru'
            self.language_config.set_language_from_environment()
            self.assertEqual(self.language_config.current_language, SupportedLanguage.RUSSIAN)
            
            # 设置中文环境变量
            os.environ['OZON_SCRAPER_LANGUAGE'] = 'zh'
            self.language_config.set_language_from_environment()
            self.assertEqual(self.language_config.current_language, SupportedLanguage.CHINESE)
            
            # 设置英语环境变量
            os.environ['OZON_SCRAPER_LANGUAGE'] = 'en'
            self.language_config.set_language_from_environment()
            self.assertEqual(self.language_config.current_language, SupportedLanguage.ENGLISH)
            
        finally:
            # 恢复原始环境变量
            if original_lang is not None:
                os.environ['OZON_SCRAPER_LANGUAGE'] = original_lang
            elif 'OZON_SCRAPER_LANGUAGE' in os.environ:
                del os.environ['OZON_SCRAPER_LANGUAGE']


if __name__ == "__main__":
    unittest.main()
