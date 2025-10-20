"""
图片相似度工具单元测试
"""

import unittest
import os
import tempfile
import numpy as np
from PIL import Image, ImageDraw
from unittest.mock import patch, Mock
import sys

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.image_similarity import (
    ProductImageSimilarity,
    load_image_from_source,
    calculate_hash_similarity,
    calculate_ssim_similarity,
    calculate_orb_similarity,
    compare_images
)


class TestImageSimilarity(unittest.TestCase):
    """图片相似度测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_images_dir = os.path.join(os.path.dirname(__file__), 'resources')
        os.makedirs(self.test_images_dir, exist_ok=True)
        
        # 创建测试图片
        self.create_test_images()
        
        # 初始化相似度工具（不使用CLIP以避免依赖问题）
        self.similarity_tool = ProductImageSimilarity(use_clip=False)
    
    def create_test_images(self):
        """创建测试用的图片"""
        # 创建相同的图片
        img1 = Image.new('RGB', (100, 100), color='red')
        self.img1_path = os.path.join(self.test_images_dir, 'test_img1.jpg')
        img1.save(self.img1_path)
        
        # 创建相同的图片（副本）
        img2 = Image.new('RGB', (100, 100), color='red')
        self.img2_path = os.path.join(self.test_images_dir, 'test_img2.jpg')
        img2.save(self.img2_path)
        
        # 创建相似的图片（稍微不同）
        img3 = Image.new('RGB', (100, 100), color='red')
        draw = ImageDraw.Draw(img3)
        draw.rectangle([10, 10, 20, 20], fill='blue')
        self.img3_path = os.path.join(self.test_images_dir, 'test_img3.jpg')
        img3.save(self.img3_path)
        
        # 创建完全不同的图片
        img4 = Image.new('RGB', (100, 100), color='blue')
        self.img4_path = os.path.join(self.test_images_dir, 'test_img4.jpg')
        img4.save(self.img4_path)
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试图片
        for img_path in [self.img1_path, self.img2_path, self.img3_path, self.img4_path]:
            if os.path.exists(img_path):
                os.remove(img_path)
    
    def test_load_image_from_local_file(self):
        """测试从本地文件加载图片"""
        img = load_image_from_source(self.img1_path)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.mode, 'RGB')
        self.assertEqual(img.size, (100, 100))
    
    def test_load_image_from_pil_object(self):
        """测试从PIL对象加载图片"""
        original_img = Image.open(self.img1_path)
        img = load_image_from_source(original_img)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.mode, 'RGB')
    
    def test_load_image_file_not_found(self):
        """测试加载不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            load_image_from_source('nonexistent_file.jpg')
    
    @patch('requests.get')
    def test_load_image_from_url(self, mock_get):
        """测试从URL加载图片"""
        # 模拟HTTP响应
        with open(self.img1_path, 'rb') as f:
            mock_response = Mock()
            mock_response.content = f.read()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
        
        img = load_image_from_source('http://example.com/test.jpg')
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.mode, 'RGB')
    
    def test_hash_similarity_identical(self):
        """测试相同图片的哈希相似度"""
        img1 = Image.open(self.img1_path)
        img2 = Image.open(self.img2_path)
        
        similarity = calculate_hash_similarity(img1, img2)
        self.assertGreaterEqual(similarity, 0.9)  # 相同图片应该有很高的相似度
    
    def test_hash_similarity_different(self):
        """测试不同图片的哈希相似度"""
        img1 = Image.open(self.img1_path)
        img4 = Image.open(self.img4_path)
        
        similarity = calculate_hash_similarity(img1, img4)
        self.assertLess(similarity, 0.8)  # 不同图片相似度应该较低
    
    def test_ssim_similarity_identical(self):
        """测试相同图片的SSIM相似度"""
        img1 = Image.open(self.img1_path)
        img2 = Image.open(self.img2_path)
        
        similarity = calculate_ssim_similarity(img1, img2)
        self.assertGreaterEqual(similarity, 0.9)  # 相同图片应该有很高的SSIM
    
    def test_ssim_similarity_different(self):
        """测试不同图片的SSIM相似度"""
        img1 = Image.open(self.img1_path)
        img4 = Image.open(self.img4_path)
        
        similarity = calculate_ssim_similarity(img1, img4)
        self.assertLess(similarity, 0.8)  # 不同图片SSIM应该较低
    
    def test_orb_similarity(self):
        """测试ORB特征匹配相似度"""
        img1 = Image.open(self.img1_path)
        img2 = Image.open(self.img2_path)
        
        similarity = calculate_orb_similarity(img1, img2)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_fast_similarity_identical(self):
        """测试快速相似度计算（相同图片）"""
        similarity = self.similarity_tool.calculate_fast_similarity(self.img1_path, self.img2_path)
        self.assertGreaterEqual(similarity, 0.9)
    
    def test_fast_similarity_different(self):
        """测试快速相似度计算（不同图片）"""
        similarity = self.similarity_tool.calculate_fast_similarity(self.img1_path, self.img4_path)
        self.assertLess(similarity, 0.8)
    
    def test_detailed_scores(self):
        """测试详细分数获取"""
        scores = self.similarity_tool.get_detailed_scores(self.img1_path, self.img2_path)
        
        # 检查返回的分数字典
        expected_keys = ['hash_similarity', 'ssim_similarity', 'orb_similarity', 'fast_combined']
        for key in expected_keys:
            self.assertIn(key, scores)
            self.assertIsInstance(scores[key], float)
            self.assertGreaterEqual(scores[key], 0.0)
            self.assertLessEqual(scores[key], 1.0)
    
    def test_compare_images_function(self):
        """测试便捷比较函数"""
        similarity = compare_images(self.img1_path, self.img2_path, method='fast', use_gpu=False)
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_invalid_method(self):
        """测试无效的计算方法"""
        with self.assertRaises(ValueError):
            self.similarity_tool.calculate_similarity(self.img1_path, self.img2_path, method='invalid')
    
    def test_similarity_range(self):
        """测试相似度分数范围"""
        # 测试多种图片组合
        test_cases = [
            (self.img1_path, self.img2_path),  # 相同
            (self.img1_path, self.img3_path),  # 相似
            (self.img1_path, self.img4_path),  # 不同
        ]
        
        for img_a, img_b in test_cases:
            similarity = self.similarity_tool.calculate_similarity(img_a, img_b, method='fast')
            self.assertGreaterEqual(similarity, 0.0)
            self.assertLessEqual(similarity, 1.0)
    
    def test_cache_clearing(self):
        """测试缓存清理"""
        # 这个测试主要确保方法可以调用而不出错
        self.similarity_tool.clear_cache()
        # 对于没有CLIP的情况，这应该不会出错


class TestCLIPSimilarity(unittest.TestCase):
    """CLIP相似度测试（需要可选依赖）"""
    
    def setUp(self):
        """测试前准备"""
        self.test_images_dir = os.path.join(os.path.dirname(__file__), 'resources')
        os.makedirs(self.test_images_dir, exist_ok=True)
        
        # 创建简单测试图片
        img = Image.new('RGB', (100, 100), color='red')
        self.img_path = os.path.join(self.test_images_dir, 'clip_test.jpg')
        img.save(self.img_path)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
    
    @unittest.skipUnless(
        os.environ.get('TEST_CLIP', '').lower() == 'true',
        "CLIP测试需要设置环境变量 TEST_CLIP=true"
    )
    def test_clip_similarity_with_dependencies(self):
        """测试CLIP相似度（需要torch和transformers）"""
        try:
            similarity_tool = ProductImageSimilarity(use_clip=True)
            if similarity_tool.use_clip:
                similarity = similarity_tool.calculate_semantic_similarity(self.img_path, self.img_path)
                self.assertGreaterEqual(similarity, 0.0)
                self.assertLessEqual(similarity, 1.0)
        except ImportError:
            self.skipTest("CLIP依赖未安装")


if __name__ == '__main__':
    # 设置日志级别
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    unittest.main()