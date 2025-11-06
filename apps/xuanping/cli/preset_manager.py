"""
配置预设管理器

负责管理配置预设的保存、加载、删除等操作
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from apps.xuanping.cli.models import UIConfig

class ConfigPreset:
    """配置预设"""
    
    def __init__(self, name: str, description: str, config: UIConfig, created_at: datetime = None):
        self.name = name
        self.description = description
        self.config = config
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'description': self.description,
            'config': self.config.to_dict(),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigPreset':
        """从字典创建预设对象"""
        return cls(
            name=data['name'],
            description=data['description'],
            config=UIConfig.from_dict(data['config']),
            created_at=datetime.fromisoformat(data['created_at'])
        )

class PresetManager:
    """预设管理器"""
    
    def __init__(self):
        self.presets_dir = Path.home() / ".xuanping" / "presets"
        self.presets_dir.mkdir(parents=True, exist_ok=True)
    
    def save_preset(self, name: str, config: UIConfig, description: str = "") -> bool:
        """保存配置预设"""
        try:
            preset = ConfigPreset(name, description, config)
            preset_file = self.presets_dir / f"{name}.json"
            
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存预设失败: {e}")
            return False
    
    def load_preset(self, name: str) -> UIConfig:
        """加载配置预设"""
        preset_file = self.presets_dir / f"{name}.json"
        
        if not preset_file.exists():
            raise FileNotFoundError(f"预设不存在: {name}")
        
        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            preset = ConfigPreset.from_dict(data)
            return preset.config
        except Exception as e:
            raise RuntimeError(f"加载预设失败: {e}")
    
    def delete_preset(self, name: str) -> bool:
        """删除配置预设"""
        try:
            preset_file = self.presets_dir / f"{name}.json"
            
            if not preset_file.exists():
                return False
            
            preset_file.unlink()
            return True
        except Exception as e:
            print(f"删除预设失败: {e}")
            return False
    
    def list_presets(self) -> List[str]:
        """列出所有预设名称"""
        try:
            presets = []
            for preset_file in self.presets_dir.glob("*.json"):
                presets.append(preset_file.stem)
            return sorted(presets)
        except Exception as e:
            print(f"列出预设失败: {e}")
            return []
    
    def get_preset_info(self, name: str) -> Dict[str, Any]:
        """获取预设详细信息"""
        preset_file = self.presets_dir / f"{name}.json"
        
        if not preset_file.exists():
            raise FileNotFoundError(f"预设不存在: {name}")
        
        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'name': data['name'],
                'description': data['description'],
                'created_at': data['created_at']
            }
        except Exception as e:
            raise RuntimeError(f"获取预设信息失败: {e}")

# 全局预设管理器实例
preset_manager = PresetManager()