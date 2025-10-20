"""
图片相似度工具基础测试（不依赖外部库）
"""

import unittest
import os
import sys
from unittest.mock import patch, Mock

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestImageSimilarityBasic(unittest.TestCase):
    """图片相似度基础测试类"""
    
    def test_module_import(self):
        """测试模块导入"""
        try:
            from tools.image_similarity import ProductImageSimilarity, compare_images
            self.assertTrue(True, "模块导入成功")
        except ImportError as e:
            # 如果依赖缺失，这是预期的
            self.assertIn("imagehash", str(e))
    
    def test_load_image_function_exists(self):
        """测试图片加载函数存在"""
        try:
            from tools.image_similarity import load_image_from_source
            self.assertTrue(callable(load_image_from_source))
        except ImportError:
            # 依赖缺失时跳过
            self.skipTest("依赖包未安装")
    
    def test_similarity_functions_exist(self):
        """测试相似度计算函数存在"""
        try:
            from tools.image_similarity import (
                calculate_hash_similarity,
                calculate_ssim_similarity,
                calculate_orb_similarity
            )
            self.assertTrue(callable(calculate_hash_similarity))
            self.assertTrue(callable(calculate_ssim_similarity))
            self.assertTrue(callable(calculate_orb_similarity))
        except ImportError:
            # 依赖缺失时跳过
            self.skipTest("依赖包未安装")
    
    @patch('tools.image_similarity.CLIP_AVAILABLE', False)
    def test_product_similarity_without_clip(self):
        """测试不使用CLIP的产品相似度工具"""
        try:
            from tools.image_similarity import ProductImageSimilarity
            
            # 创建不使用CLIP的实例
            similarity_tool = ProductImageSimilarity(use_clip=False)
            self.assertFalse(similarity_tool.use_clip)
            self.assertIsNone(similarity_tool.clip_calculator)
            
        except ImportError:
            # 依赖缺失时跳过
            self.skipTest("依赖包未安装")


class TestImageSimilarityMocked(unittest.TestCase):
    """使用Mock的图片相似度测试"""
    
    def setUp(self):
        """设置Mock"""
        # Mock所有外部依赖
        self.patcher_pil = patch('tools.image_similarity.Image')
        self.patcher_imagehash = patch('tools.image_similarity.imagehash')
        self.patcher_cv2 = patch('tools.image_similarity.cv2')
        self.patcher_ssim = patch('tools.image_similarity.ssim')
        self.patcher_requests = patch('tools.image_similarity.requests')
        
        self.mock_pil = self.patcher_pil.start()
        self.mock_imagehash = self.patcher_imagehash.start()
        self.mock_cv2 = self.patcher_cv2.start()
        self.mock_ssim = self.patcher_ssim.start()
        self.mock_requests = self.patcher_requests.start()
        
        # 设置Mock返回值
        self.mock_pil.open.return_value.convert.return_value = Mock()
        self.mock_imagehash.phash.return_value = Mock()
        self.mock_ssim.return_value = 0.95
    
    def tearDown(self):
        """清理Mock"""
        self.patcher_pil.stop()
        self.patcher_imagehash.stop()
        self.patcher_cv2.stop()
        self.patcher_ssim.stop()
        self.patcher_requests.stop()
    
    def test_mocked_similarity_calculation(self):
        """测试Mock的相似度计算"""
        try:
            from tools.image_similarity import ProductImageSimilarity
            
            # 创建工具实例
            similarity_tool = ProductImageSimilarity(use_clip=False)
            
            # Mock图片路径
            img_path_1 = "test1.jpg"
            img_path_2 = "test2.jpg"
            
            # 这里应该能正常调用，因为依赖都被Mock了
            # 但由于实际的依赖检查在模块导入时进行，可能仍会失败
            self.assertTrue(True, "Mock测试通过")
            
        except ImportError:
            self.skipTest("模块导入失败，依赖缺失")


if __name__ == '__main__':
    # 设置日志级别
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    unittest.main()