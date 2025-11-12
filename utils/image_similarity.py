"""
图片相似度评分工具
支持基于哈希、SSIM、ORB特征匹配和CLIP语义相似度的多层次图片相似度评分
适用于商品图片相似度检测，支持CPU/GPU加速
"""

import os
import numpy as np
from PIL import Image, ImageOps
import imagehash
from skimage.metrics import structural_similarity as ssim
import cv2
import requests
from io import BytesIO
from typing import Union, Tuple, Optional
import logging

# 可选依赖
try:
    import torch
    from transformers import CLIPModel, CLIPProcessor

    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    torch = None
    CLIPModel = None
    CLIPProcessor = None

logger = logging.getLogger(__name__)


def load_image_from_source(source: Union[str, Image.Image]) -> Image.Image:
    """
    从多种来源加载图片
    
    Args:
        source: 图片来源，可以是：
               - 本地文件路径
               - HTTP/HTTPS URL
               - PIL Image对象
    
    Returns:
        PIL Image对象 (RGB格式)
    """
    if isinstance(source, Image.Image):
        return source.convert('RGB')

    if isinstance(source, str):
        # 判断是URL还是本地路径
        if source.startswith(('http://', 'https://')):
            try:
                response = requests.get(source, timeout=10)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                return img.convert('RGB')
            except Exception as e:
                raise ValueError(f"无法从URL加载图片 {source}: {e}")
        else:
            # 本地文件路径
            if not os.path.exists(source):
                raise FileNotFoundError(f"图片文件不存在: {source}")
            try:
                img = Image.open(source)
                return img.convert('RGB')
            except Exception as e:
                raise ValueError(f"无法加载本地图片 {source}: {e}")

    raise ValueError(f"不支持的图片来源类型: {type(source)}")


def preprocess_for_ssim(img_a: Image.Image, img_b: Image.Image, size: int = 512) -> Tuple[np.ndarray, np.ndarray]:
    """
    为SSIM计算预处理图片
    
    Args:
        img_a, img_b: 输入图片
        size: 统一尺寸
    
    Returns:
        处理后的灰度图片数组
    """
    # 转换为灰度图
    gray_a = img_a.convert('L')
    gray_b = img_b.convert('L')

    # 统一尺寸，保持宽高比
    gray_a = ImageOps.contain(gray_a, (size, size))
    gray_b = ImageOps.contain(gray_b, (size, size))

    # 转换为numpy数组
    arr_a = np.array(gray_a)
    arr_b = np.array(gray_b)

    # 裁剪到相同尺寸
    min_h = min(arr_a.shape[0], arr_b.shape[0])
    min_w = min(arr_a.shape[1], arr_b.shape[1])

    arr_a = arr_a[:min_h, :min_w]
    arr_b = arr_b[:min_h, :min_w]

    return arr_a, arr_b


def calculate_hash_similarity(img_a: Image.Image, img_b: Image.Image, hash_type: str = 'phash') -> float:
    """
    计算感知哈希相似度
    
    Args:
        img_a, img_b: 输入图片
        hash_type: 哈希类型 ('phash', 'dhash', 'whash', 'ahash')
    
    Returns:
        相似度分数 (0-1)
    """
    hash_funcs = {
        'phash': imagehash.phash,
        'dhash': imagehash.dhash,
        'whash': imagehash.whash,
        'ahash': imagehash.average_hash
    }

    if hash_type not in hash_funcs:
        raise ValueError(f"不支持的哈希类型: {hash_type}")

    hash_func = hash_funcs[hash_type]

    hash_a = hash_func(img_a)
    hash_b = hash_func(img_b)

    # 计算汉明距离
    hamming_distance = abs(hash_a - hash_b)

    # 转换为相似度 (0-1)
    hash_size = len(str(hash_a)) * 4  # 每个十六进制字符代表4位
    similarity = max(0.0, 1.0 - hamming_distance / hash_size)

    return float(similarity)


def calculate_ssim_similarity(img_a: Image.Image, img_b: Image.Image) -> float:
    """
    计算结构相似度(SSIM)
    
    Args:
        img_a, img_b: 输入图片
    
    Returns:
        SSIM相似度分数 (0-1)
    """
    arr_a, arr_b = preprocess_for_ssim(img_a, img_b)

    # 计算SSIM
    similarity = ssim(arr_a, arr_b, data_range=255)

    # 确保在[0,1]范围内
    return float(np.clip(similarity, 0.0, 1.0))


def calculate_orb_similarity(img_a: Image.Image, img_b: Image.Image, max_features: int = 1000) -> float:
    """
    计算ORB特征匹配相似度
    
    Args:
        img_a, img_b: 输入图片
        max_features: 最大特征点数量
    
    Returns:
        ORB相似度分数 (0-1)
    """
    # 转换为OpenCV格式
    arr_a = cv2.cvtColor(np.array(img_a), cv2.COLOR_RGB2GRAY)
    arr_b = cv2.cvtColor(np.array(img_b), cv2.COLOR_RGB2GRAY)

    # 创建ORB检测器
    orb = cv2.ORB_create(max_features)

    # 检测关键点和描述符
    kp_a, desc_a = orb.detectAndCompute(arr_a, None)
    kp_b, desc_b = orb.detectAndCompute(arr_b, None)

    if desc_a is None or desc_b is None:
        return 0.0

    # 使用BF匹配器
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    try:
        matches = bf.knnMatch(desc_a, desc_b, k=2)
    except cv2.error:
        return 0.0

    # 应用Lowe's ratio test筛选好的匹配
    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

    # 归一化到[0,1]，基于经验值200作为满分
    similarity = min(1.0, len(good_matches) / 200.0)

    return float(similarity)


class CLIPSimilarityCalculator:
    """CLIP语义相似度计算器"""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: Optional[str] = None):
        if not CLIP_AVAILABLE:
            raise ImportError("CLIP功能需要安装torch和transformers: pip install torch transformers")

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.cache = {}

        logger.info(f"初始化CLIP模型: {model_name}, 设备: {self.device}")

    def _load_model(self):
        """延迟加载模型"""
        if self.model is None:
            try:
                self.model = CLIPModel.from_pretrained(self.model_name).to(self.device)
                self.processor = CLIPProcessor.from_pretrained(self.model_name)
                logger.info("CLIP模型加载成功")
            except Exception as e:
                logger.error(f"CLIP模型加载失败: {e}")
                raise

    def _get_image_embedding(self, img: Image.Image) -> np.ndarray:
        """获取图片的CLIP嵌入向量"""
        self._load_model()

        # 简单缓存机制（基于图片对象ID）
        img_id = id(img)
        if img_id in self.cache:
            return self.cache[img_id]

        # 预处理图片
        inputs = self.processor(images=img, return_tensors="pt").to(self.device)

        # 获取图片特征
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            # L2归一化
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        # 转换为numpy数组并缓存
        embedding = image_features.cpu().numpy()[0]
        self.cache[img_id] = embedding

        return embedding

    def calculate_similarity(self, img_a: Image.Image, img_b: Image.Image) -> float:
        """
        计算两张图片的CLIP语义相似度
        
        Args:
            img_a, img_b: 输入图片
        
        Returns:
            语义相似度分数 (0-1)
        """
        embedding_a = self._get_image_embedding(img_a)
        embedding_b = self._get_image_embedding(img_b)

        # 计算余弦相似度
        cosine_sim = float(np.dot(embedding_a, embedding_b))

        # 将余弦相似度从[-1,1]映射到[0,1]
        similarity = (cosine_sim + 1.0) / 2.0

        return similarity

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


class ProductImageSimilarity:
    """商品图片相似度评分工具"""

    def __init__(self,
                 use_clip: bool = True,
                 clip_model: str = "openai/clip-vit-base-patch32",
                 device: Optional[str] = None):
        """
        初始化图片相似度工具
        
        Args:
            use_clip: 是否使用CLIP语义相似度
            clip_model: CLIP模型名称
            device: 计算设备 ('cpu', 'cuda', None为自动选择)
        """
        self.use_clip = use_clip and CLIP_AVAILABLE
        self.clip_calculator = None

        if self.use_clip:
            try:
                self.clip_calculator = CLIPSimilarityCalculator(clip_model, device)
                logger.info("CLIP语义相似度功能已启用")
            except Exception as e:
                logger.warning(f"CLIP初始化失败，将使用传统方法: {e}")
                self.use_clip = False

        if not self.use_clip:
            logger.info("使用传统图片相似度方法（哈希+SSIM+ORB）")

    def calculate_fast_similarity(self,
                                  source_a: Union[str, Image.Image],
                                  source_b: Union[str, Image.Image]) -> float:
        """
        快速相似度计算（哈希+SSIM）
        
        Args:
            source_a, source_b: 图片来源
        
        Returns:
            快速相似度分数 (0-1)
        """
        img_a = load_image_from_source(source_a)
        img_b = load_image_from_source(source_b)

        # 计算哈希相似度
        hash_sim = calculate_hash_similarity(img_a, img_b, 'phash')

        # 计算SSIM相似度
        ssim_sim = calculate_ssim_similarity(img_a, img_b)

        # 加权组合 (经验权重)
        combined_score = 0.6 * hash_sim + 0.4 * ssim_sim

        return float(combined_score)

    def calculate_semantic_similarity(self,
                                      source_a: Union[str, Image.Image],
                                      source_b: Union[str, Image.Image]) -> float:
        """
        语义相似度计算（快速方法+CLIP+ORB）
        
        Args:
            source_a, source_b: 图片来源
        
        Returns:
            语义相似度分数 (0-1)
        """
        img_a = load_image_from_source(source_a)
        img_b = load_image_from_source(source_b)

        # 先计算快速相似度
        fast_score = self.calculate_fast_similarity(img_a, img_b)

        # 如果快速相似度很高，直接返回
        if fast_score >= 0.9 or not self.use_clip:
            return fast_score

        # 计算CLIP语义相似度
        clip_score = self.clip_calculator.calculate_similarity(img_a, img_b)

        # 如果快速方法和CLIP分歧较大，使用ORB作为补充
        orb_score = 0.0
        if abs(fast_score - clip_score) > 0.25:
            orb_score = calculate_orb_similarity(img_a, img_b)

        # 综合评分
        if orb_score > 0:
            # 三种方法加权组合
            combined_score = 0.4 * fast_score + 0.4 * clip_score + 0.2 * orb_score
        else:
            # 两种方法加权组合
            combined_score = 0.5 * fast_score + 0.5 * clip_score

        return float(combined_score)

    def calculate_similarity(self,
                             source_a: Union[str, Image.Image],
                             source_b: Union[str, Image.Image],
                             method: str = 'auto') -> float:
        """
        计算图片相似度
        
        Args:
            source_a, source_b: 图片来源（URL、本地路径或PIL Image对象）
            method: 计算方法 ('fast', 'semantic', 'auto')
        
        Returns:
            相似度分数 (0-1)
        """
        if method == 'fast':
            return self.calculate_fast_similarity(source_a, source_b)
        elif method == 'semantic':
            return self.calculate_semantic_similarity(source_a, source_b)
        elif method == 'auto':
            # 自动选择：有CLIP用语义，否则用快速
            if self.use_clip:
                return self.calculate_semantic_similarity(source_a, source_b)
            else:
                return self.calculate_fast_similarity(source_a, source_b)
        else:
            raise ValueError(f"不支持的计算方法: {method}")

    def get_detailed_scores(self,
                            source_a: Union[str, Image.Image],
                            source_b: Union[str, Image.Image]) -> dict:
        """
        获取详细的各项相似度分数
        
        Args:
            source_a, source_b: 图片来源
        
        Returns:
            包含各项分数的字典
        """
        img_a = load_image_from_source(source_a)
        img_b = load_image_from_source(source_b)

        scores = {
            'hash_similarity': calculate_hash_similarity(img_a, img_b, 'phash'),
            'ssim_similarity': calculate_ssim_similarity(img_a, img_b),
            'orb_similarity': calculate_orb_similarity(img_a, img_b),
        }

        # 快速组合分数
        scores['fast_combined'] = 0.6 * scores['hash_similarity'] + 0.4 * scores['ssim_similarity']

        # CLIP语义分数（如果可用）
        if self.use_clip:
            scores['clip_similarity'] = self.clip_calculator.calculate_similarity(img_a, img_b)

            # 语义组合分数
            if abs(scores['fast_combined'] - scores['clip_similarity']) > 0.25:
                scores['semantic_combined'] = (0.4 * scores['fast_combined'] +
                                               0.4 * scores['clip_similarity'] +
                                               0.2 * scores['orb_similarity'])
            else:
                scores['semantic_combined'] = (0.5 * scores['fast_combined'] +
                                               0.5 * scores['clip_similarity'])
        else:
            scores['clip_similarity'] = None
            scores['semantic_combined'] = scores['fast_combined']

        return scores

    def clear_cache(self):
        """清空CLIP缓存"""
        if self.clip_calculator:
            self.clip_calculator.clear_cache()


# 便捷函数
def compare_images(source_a: Union[str, Image.Image],
                   source_b: Union[str, Image.Image],
                   method: str = 'auto',
                   use_gpu: bool = None) -> float:
    """
    便捷的图片相似度比较函数
    
    Args:
        source_a, source_b: 图片来源（URL、本地路径或PIL Image对象）
        method: 计算方法 ('fast', 'semantic', 'auto')
        use_gpu: 是否使用GPU（None为自动检测）
    
    Returns:
        相似度分数 (0-1)
    """
    device = None
    if use_gpu is not None:
        device = "cuda" if use_gpu else "cpu"

    similarity_tool = ProductImageSimilarity(use_clip=True, device=device)
    return similarity_tool.calculate_similarity(source_a, source_b, method)


if __name__ == "__main__":
    # 示例用法
    import sys

    if len(sys.argv) != 3:
        print("用法: python image_similarity.py <图片1> <图片2>")
        print("支持本地文件路径或HTTP URL")
        sys.exit(1)

    img1_path = sys.argv[1]
    img2_path = sys.argv[2]

    print(f"比较图片相似度:")
    print(f"图片1: {img1_path}")
    print(f"图片2: {img2_path}")
    print("-" * 50)

    try:
        # 创建相似度工具
        similarity_tool = ProductImageSimilarity(use_clip=True)

        # 获取详细分数
        scores = similarity_tool.get_detailed_scores(img1_path, img2_path)

        print("详细相似度分数:")
        for score_name, score_value in scores.items():
            if score_value is not None:
                print(f"  {score_name}: {score_value:.4f}")

        print("-" * 50)

        # 最终相似度
        final_score = similarity_tool.calculate_similarity(img1_path, img2_path)
        print(f"最终相似度: {final_score:.4f}")

        # 相似度解释
        if final_score >= 0.9:
            print("解释: 图片高度相似（可能是近重复）")
        elif final_score >= 0.8:
            print("解释: 图片很相似（可能是同一商品的不同图片）")
        elif final_score >= 0.65:
            print("解释: 图片较相似（可能是同类商品）")
        else:
            print("解释: 图片相似度较低")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
