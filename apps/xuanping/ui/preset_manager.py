"""
配置预设管理器

提供配置预设的保存、加载、删除和管理功能
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .models import UIConfig, ConfigPreset


class PresetManager:
    """配置预设管理器"""
    
    def __init__(self, presets_dir: Optional[str] = None):
        """
        初始化预设管理器
        
        Args:
            presets_dir: 预设文件存储目录，默认为用户目录下的.xuanping/presets
        """
        if presets_dir is None:
            home_dir = Path.home()
            self.presets_dir = home_dir / ".xuanping" / "presets"
        else:
            self.presets_dir = Path(presets_dir)
        
        # 确保预设目录存在
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        
        # 预设文件路径
        self.presets_file = self.presets_dir / "presets.json"
        
        # 加载现有预设
        self._presets: Dict[str, ConfigPreset] = {}
        self._load_presets()
    
    def save_preset(self, name: str, description: str, config: UIConfig) -> bool:
        """
        保存配置预设
        
        Args:
            name: 预设名称
            description: 预设描述
            config: 配置对象
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 创建预设对象
            preset = ConfigPreset(
                name=name,
                description=description,
                config=config,
                created_at=datetime.now()
            )
            
            # 添加到内存中的预设字典
            self._presets[name] = preset
            
            # 保存到文件
            return self._save_presets()
            
        except Exception as e:
            print(f"保存预设失败: {e}")
            return False
    
    def load_preset(self, name: str) -> Optional[ConfigPreset]:
        """
        加载指定名称的预设
        
        Args:
            name: 预设名称
            
        Returns:
            ConfigPreset: 预设对象，如果不存在则返回None
        """
        return self._presets.get(name)
    
    def delete_preset(self, name: str) -> bool:
        """
        删除指定名称的预设
        
        Args:
            name: 预设名称
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if name in self._presets:
                del self._presets[name]
                return self._save_presets()
            return True
            
        except Exception as e:
            print(f"删除预设失败: {e}")
            return False
    
    def list_presets(self) -> List[ConfigPreset]:
        """
        获取所有预设列表
        
        Returns:
            List[ConfigPreset]: 预设列表，按创建时间排序
        """
        presets = list(self._presets.values())
        presets.sort(key=lambda x: x.created_at, reverse=True)
        return presets
    
    def preset_exists(self, name: str) -> bool:
        """
        检查预设是否存在
        
        Args:
            name: 预设名称
            
        Returns:
            bool: 预设是否存在
        """
        return name in self._presets
    
    def get_preset_names(self) -> List[str]:
        """
        获取所有预设名称
        
        Returns:
            List[str]: 预设名称列表
        """
        return list(self._presets.keys())
    
    def export_preset(self, name: str, export_path: str) -> bool:
        """
        导出预设到指定文件
        
        Args:
            name: 预设名称
            export_path: 导出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            preset = self._presets.get(name)
            if not preset:
                return False
            
            export_data = {
                'preset': preset.to_dict(),
                'exported_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"导出预设失败: {e}")
            return False
    
    def import_preset(self, import_path: str, overwrite: bool = False) -> Optional[str]:
        """
        从文件导入预设
        
        Args:
            import_path: 导入文件路径
            overwrite: 是否覆盖同名预设
            
        Returns:
            Optional[str]: 导入的预设名称，失败返回None
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            preset_data = import_data.get('preset')
            if not preset_data:
                return None
            
            preset = ConfigPreset.from_dict(preset_data)
            
            # 检查是否已存在同名预设
            if self.preset_exists(preset.name) and not overwrite:
                # 生成新名称
                base_name = preset.name
                counter = 1
                while self.preset_exists(f"{base_name}_{counter}"):
                    counter += 1
                preset.name = f"{base_name}_{counter}"
            
            # 保存预设
            self._presets[preset.name] = preset
            self._save_presets()
            
            return preset.name
            
        except Exception as e:
            print(f"导入预设失败: {e}")
            return None
    
    def create_default_presets(self):
        """创建默认预设"""
        # 默认预设1：标准筛选
        default_config_1 = UIConfig(
            margin=0.1,
            item_created_days=150,
            follow_buy_cnt=37,
            max_monthly_sold=0,
            monthly_sold_min=100,
            item_min_weight=0,
            item_max_weight=1000,
            g01_item_min_price=0,
            g01_item_max_price=1000,
            max_products_per_store=50,
            output_format="xlsx"
        )
        
        if not self.preset_exists("标准筛选"):
            self.save_preset(
                "标准筛选",
                "适用于大多数场景的标准筛选配置",
                default_config_1
            )
        
        # 默认预设2：严格筛选
        default_config_2 = UIConfig(
            margin=0.15,
            item_created_days=100,
            follow_buy_cnt=20,
            max_monthly_sold=5,
            monthly_sold_min=50,
            item_min_weight=0,
            item_max_weight=500,
            g01_item_min_price=100,
            g01_item_max_price=800,
            max_products_per_store=30,
            output_format="xlsx"
        )
        
        if not self.preset_exists("严格筛选"):
            self.save_preset(
                "严格筛选",
                "更严格的筛选条件，适用于高质量商品筛选",
                default_config_2
            )
        
        # 默认预设3：宽松筛选
        default_config_3 = UIConfig(
            margin=0.05,
            item_created_days=300,
            follow_buy_cnt=50,
            max_monthly_sold=0,
            monthly_sold_min=200,
            item_min_weight=0,
            item_max_weight=2000,
            g01_item_min_price=0,
            g01_item_max_price=2000,
            max_products_per_store=100,
            output_format="xlsx"
        )
        
        if not self.preset_exists("宽松筛选"):
            self.save_preset(
                "宽松筛选",
                "较宽松的筛选条件，适用于大批量商品筛选",
                default_config_3
            )
    
    def _load_presets(self):
        """从文件加载预设"""
        try:
            if self.presets_file.exists():
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for preset_data in data.get('presets', []):
                    preset = ConfigPreset.from_dict(preset_data)
                    self._presets[preset.name] = preset
            else:
                # 如果预设文件不存在，创建默认预设
                self.create_default_presets()
                
        except Exception as e:
            print(f"加载预设失败: {e}")
            # 创建默认预设作为备用
            self.create_default_presets()
    
    def _save_presets(self) -> bool:
        """保存预设到文件"""
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'presets': [preset.to_dict() for preset in self._presets.values()]
            }
            
            # 先写入临时文件，然后重命名，确保原子性操作
            temp_file = self.presets_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 重命名临时文件
            temp_file.replace(self.presets_file)
            
            return True
            
        except Exception as e:
            print(f"保存预设失败: {e}")
            return False
    
    def backup_presets(self, backup_path: Optional[str] = None) -> bool:
        """
        备份所有预设
        
        Args:
            backup_path: 备份文件路径，默认为预设目录下的backup_YYYYMMDD_HHMMSS.json
            
        Returns:
            bool: 备份是否成功
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.presets_dir / f"backup_{timestamp}.json"
            
            backup_data = {
                'version': '1.0',
                'backup_time': datetime.now().isoformat(),
                'presets': [preset.to_dict() for preset in self._presets.values()]
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"备份预设失败: {e}")
            return False
    
    def restore_presets(self, backup_path: str, merge: bool = True) -> bool:
        """
        从备份恢复预设
        
        Args:
            backup_path: 备份文件路径
            merge: 是否与现有预设合并，False表示完全替换
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            if not merge:
                self._presets.clear()
            
            for preset_data in backup_data.get('presets', []):
                preset = ConfigPreset.from_dict(preset_data)
                self._presets[preset.name] = preset
            
            return self._save_presets()
            
        except Exception as e:
            print(f"恢复预设失败: {e}")
            return False


# 全局预设管理器实例
preset_manager = PresetManager()