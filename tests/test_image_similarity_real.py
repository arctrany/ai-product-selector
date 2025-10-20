"""
图片相似度工具实际素材测试
使用真实图片素材测试相似度工具的实际效果
"""

import unittest
import os
import sys
import requests
from io import BytesIO
from PIL import Image

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from tools.image_similarity import ProductImageSimilarity, compare_images
    SIMILARITY_AVAILABLE = True
except ImportError as e:
    print(f"图片相似度工具导入失败: {e}")
    SIMILARITY_AVAILABLE = False

class TestImageSimilarityReal(unittest.TestCase):
    """使用真实素材的图片相似度测试"""
    
    def setUp(self):
        """测试前准备"""
        if not SIMILARITY_AVAILABLE:
            self.skipTest("图片相似度工具不可用，请安装依赖包")
        
        self.test_images_dir = os.path.join(os.path.dirname(__file__), 'resources')
        os.makedirs(self.test_images_dir, exist_ok=True)
        
        # 准备测试图片URL（使用一些公开的示例图片）
        self.test_images = {
            'red_apple': 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop',
            'green_apple': 'https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=300&h=300&fit=crop',
            'orange': 'https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=300&h=300&fit=crop',
            'banana': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300&h=300&fit=crop'
        }
        
        # 下载测试图片
        self.downloaded_images = {}
        self.download_test_images()
        
        # 创建本地测试图片
        self.create_local_test_images()
        
        # 初始化相似度工具
        self.similarity_tool = ProductImageSimilarity(use_clip=False)  # 先不使用CLIP避免依赖问题
    
    def download_test_images(self):
        """下载测试图片"""
        for name, url in self.test_images.items():
            try:
                print(f"正在下载测试图片: {name}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # 保存图片
                img_path = os.path.join(self.test_images_dir, f'{name}.jpg')
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                self.downloaded_images[name] = img_path
                print(f"下载成功: {img_path}")
                
            except Exception as e:
                print(f"下载图片 {name} 失败: {e}")
                # 如果下载失败，创建占位图片
                self.create_placeholder_image(name)
    
    def create_placeholder_image(self, name):
        """创建占位图片"""
        colors = {
            'red_apple': 'red',
            'green_apple': 'green', 
            'orange': 'orange',
            'banana': 'yellow'
        }
        
        color = colors.get(name, 'gray')
        img = Image.new('RGB', (300, 300), color=color)
        img_path = os.path.join(self.test_images_dir, f'{name}.jpg')
        img.save(img_path)
        self.downloaded_images[name] = img_path
        print(f"创建占位图片: {img_path}")
    
    def create_local_test_images(self):
        """创建本地测试图片"""
        # 创建相同的图片对
        img1 = Image.new('RGB', (200, 200), color='blue')
        self.identical_img1 = os.path.join(self.test_images_dir, 'identical_1.jpg')
        img1.save(self.identical_img1)
        
        img2 = Image.new('RGB', (200, 200), color='blue')
        self.identical_img2 = os.path.join(self.test_images_dir, 'identical_2.jpg')
        img2.save(self.identical_img2)
        
        # 创建相似的图片（稍有差异）
        img3 = Image.new('RGB', (200, 200), color='blue')
        # 添加小的白色方块
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img3)
        draw.rectangle([90, 90, 110, 110], fill='white')
        self.similar_img = os.path.join(self.test_images_dir, 'similar.jpg')
        img3.save(self.similar_img)
        
        # 创建完全不同的图片
        img4 = Image.new('RGB', (200, 200), color='purple')
        self.different_img = os.path.join(self.test_images_dir, 'different.jpg')
        img4.save(self.different_img)
    
    def tearDown(self):
        """测试后清理"""
        # 清理下载的图片
        for img_path in self.downloaded_images.values():
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except:
                    pass
        
        # 清理本地创建的图片
        local_images = [self.identical_img1, self.identical_img2, self.similar_img, self.different_img]
        for img_path in local_images:
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except:
                    pass
    
    def test_identical_images_similarity(self):
        """测试相同图片的相似度"""
        similarity = self.similarity_tool.calculate_similarity(
            self.identical_img1, self.identical_img2, method='fast'
        )
        print(f"相同图片相似度: {similarity:.4f}")
        self.assertGreaterEqual(similarity, 0.9, "相同图片的相似度应该很高")
    
    def test_similar_images_similarity(self):
        """测试相似图片的相似度"""
        similarity = self.similarity_tool.calculate_similarity(
            self.identical_img1, self.similar_img, method='fast'
        )
        print(f"相似图片相似度: {similarity:.4f}")
        self.assertGreaterEqual(similarity, 0.5, "相似图片应该有中等相似度")
        self.assertLess(similarity, 0.9, "相似图片相似度不应该太高")
    
    def test_different_images_similarity(self):
        """测试不同图片的相似度"""
        similarity = self.similarity_tool.calculate_similarity(
            self.identical_img1, self.different_img, method='fast'
        )
        print(f"不同图片相似度: {similarity:.4f}")
        self.assertLess(similarity, 0.7, "不同图片的相似度应该较低")
    
    def test_fruit_images_similarity(self):
        """测试水果图片相似度"""
        if len(self.downloaded_images) < 2:
            self.skipTest("测试图片下载不足")
        
        # 测试苹果之间的相似度（应该较高）
        if 'red_apple' in self.downloaded_images and 'green_apple' in self.downloaded_images:
            apple_similarity = self.similarity_tool.calculate_similarity(
                self.downloaded_images['red_apple'],
                self.downloaded_images['green_apple'],
                method='fast'
            )
            print(f"红苹果 vs 青苹果相似度: {apple_similarity:.4f}")
            
        # 测试苹果和香蕉的相似度（应该较低）
        if 'red_apple' in self.downloaded_images and 'banana' in self.downloaded_images:
            apple_banana_similarity = self.similarity_tool.calculate_similarity(
                self.downloaded_images['red_apple'],
                self.downloaded_images['banana'],
                method='fast'
            )
            print(f"红苹果 vs 香蕉相似度: {apple_banana_similarity:.4f}")
    
    def test_detailed_scores_analysis(self):
        """测试详细分数分析"""
        if len(self.downloaded_images) < 2:
            self.skipTest("测试图片下载不足")
        
        # 选择两张图片进行详细分析
        img_names = list(self.downloaded_images.keys())
        if len(img_names) >= 2:
            img1_path = self.downloaded_images[img_names[0]]
            img2_path = self.downloaded_images[img_names[1]]
            
            scores = self.similarity_tool.get_detailed_scores(img1_path, img2_path)
            
            print(f"\n详细相似度分析 ({img_names[0]} vs {img_names[1]}):")
            print("-" * 50)
            for score_name, score_value in scores.items():
                if score_value is not None:
                    print(f"{score_name:20}: {score_value:.4f}")
            
            # 验证分数范围
            for score_name, score_value in scores.items():
                if score_value is not None:
                    self.assertGreaterEqual(score_value, 0.0, f"{score_name} 分数应该 >= 0")
                    self.assertLessEqual(score_value, 1.0, f"{score_name} 分数应该 <= 1")
    
    def test_performance_comparison(self):
        """测试性能对比"""
        import time
        
        # 使用本地图片测试性能
        img1 = self.identical_img1
        img2 = self.similar_img
        
        # 测试快速模式性能
        start_time = time.time()
        fast_similarity = self.similarity_tool.calculate_similarity(img1, img2, method='fast')
        fast_time = time.time() - start_time
        
        print(f"\n性能测试结果:")
        print(f"快速模式: {fast_similarity:.4f} (耗时: {fast_time:.3f}s)")
        
        # 如果有CLIP，也测试语义模式
        if self.similarity_tool.use_clip:
            start_time = time.time()
            semantic_similarity = self.similarity_tool.calculate_similarity(img1, img2, method='semantic')
            semantic_time = time.time() - start_time
            print(f"语义模式: {semantic_similarity:.4f} (耗时: {semantic_time:.3f}s)")
        else:
            print("语义模式: 未启用 (需要CLIP依赖)")

if __name__ == '__main__':
    # 设置日志级别
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("开始图片相似度工具实际测试...")
    print("=" * 60)
    
    unittest.main(verbosity=2)