"""
页面元素数据模型

定义页面元素的数据结构和操作接口
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class ElementType(Enum):
    """元素类型枚举"""
    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    TEXT = "text"
    IMAGE = "image"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    DIV = "div"
    SPAN = "span"
    TABLE = "table"
    FORM = "form"
    UNKNOWN = "unknown"


class ElementState(Enum):
    """元素状态枚举"""
    VISIBLE = "visible"
    HIDDEN = "hidden"
    ENABLED = "enabled"
    DISABLED = "disabled"
    CHECKED = "checked"
    UNCHECKED = "unchecked"
    FOCUSED = "focused"
    SELECTED = "selected"


@dataclass
class ElementBounds:
    """元素边界信息"""
    x: float
    y: float
    width: float
    height: float
    
    @property
    def center_x(self) -> float:
        """中心点X坐标"""
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        """中心点Y坐标"""
        return self.y + self.height / 2
    
    @property
    def area(self) -> float:
        """元素面积"""
        return self.width * self.height
    
    def contains_point(self, x: float, y: float) -> bool:
        """判断点是否在元素内"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)


@dataclass
class ElementAttributes:
    """元素属性集合"""
    tag_name: str = ""
    id: str = ""
    class_name: str = ""
    name: str = ""
    value: str = ""
    href: str = ""
    src: str = ""
    alt: str = ""
    title: str = ""
    placeholder: str = ""
    type: str = ""
    role: str = ""
    aria_label: str = ""
    data_attributes: Dict[str, str] = field(default_factory=dict)
    custom_attributes: Dict[str, str] = field(default_factory=dict)
    
    def get_attribute(self, name: str) -> Optional[str]:
        """获取属性值"""
        # 标准属性
        if hasattr(self, name):
            return getattr(self, name)
        
        # data属性
        if name.startswith('data-'):
            return self.data_attributes.get(name)
        
        # 自定义属性
        return self.custom_attributes.get(name)
    
    def set_attribute(self, name: str, value: str) -> None:
        """设置属性值"""
        if name.startswith('data-'):
            self.data_attributes[name] = value
        elif hasattr(self, name):
            setattr(self, name, value)
        else:
            self.custom_attributes[name] = value


@dataclass
class PageElement:
    """页面元素主类"""
    
    # 基础信息
    selector: str
    element_type: ElementType = ElementType.UNKNOWN
    attributes: ElementAttributes = field(default_factory=ElementAttributes)
    
    # 内容信息
    text_content: str = ""
    inner_html: str = ""
    outer_html: str = ""
    
    # 位置信息
    bounds: Optional[ElementBounds] = None
    
    # 状态信息
    states: List[ElementState] = field(default_factory=list)
    
    # 层级信息
    parent_selector: Optional[str] = None
    children_selectors: List[str] = field(default_factory=list)
    
    # 元数据
    screenshot_data: Optional[bytes] = None
    xpath: Optional[str] = None
    css_selector: Optional[str] = None
    
    # 扩展信息
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """后处理"""
        # 根据标签名推断元素类型
        if self.element_type == ElementType.UNKNOWN and self.attributes.tag_name:
            self.element_type = self._infer_element_type()
    
    def _infer_element_type(self) -> ElementType:
        """根据标签名和属性推断元素类型"""
        tag = self.attributes.tag_name.lower()
        type_attr = self.attributes.type.lower()
        
        type_mapping = {
            'button': ElementType.BUTTON,
            'a': ElementType.LINK,
            'img': ElementType.IMAGE,
            'select': ElementType.SELECT,
            'textarea': ElementType.TEXTAREA,
            'div': ElementType.DIV,
            'span': ElementType.SPAN,
            'table': ElementType.TABLE,
            'form': ElementType.FORM,
        }
        
        if tag == 'input':
            input_type_mapping = {
                'text': ElementType.INPUT,
                'password': ElementType.INPUT,
                'email': ElementType.INPUT,
                'number': ElementType.INPUT,
                'checkbox': ElementType.CHECKBOX,
                'radio': ElementType.RADIO,
                'button': ElementType.BUTTON,
                'submit': ElementType.BUTTON,
            }
            return input_type_mapping.get(type_attr, ElementType.INPUT)
        
        return type_mapping.get(tag, ElementType.UNKNOWN)
    
    def has_state(self, state: ElementState) -> bool:
        """检查是否具有指定状态"""
        return state in self.states
    
    def add_state(self, state: ElementState) -> None:
        """添加状态"""
        if state not in self.states:
            self.states.append(state)
    
    def remove_state(self, state: ElementState) -> None:
        """移除状态"""
        if state in self.states:
            self.states.remove(state)
    
    def is_visible(self) -> bool:
        """是否可见"""
        return ElementState.VISIBLE in self.states
    
    def is_enabled(self) -> bool:
        """是否启用"""
        return ElementState.ENABLED in self.states
    
    def is_clickable(self) -> bool:
        """是否可点击"""
        return (self.is_visible() and 
                self.is_enabled() and 
                self.element_type in [ElementType.BUTTON, ElementType.LINK])
    
    def is_input_element(self) -> bool:
        """是否为输入元素"""
        return self.element_type in [
            ElementType.INPUT, 
            ElementType.TEXTAREA, 
            ElementType.SELECT
        ]
    
    def get_display_text(self) -> str:
        """获取显示文本"""
        if self.text_content:
            return self.text_content.strip()
        elif self.attributes.value:
            return self.attributes.value
        elif self.attributes.alt:
            return self.attributes.alt
        elif self.attributes.title:
            return self.attributes.title
        elif self.attributes.aria_label:
            return self.attributes.aria_label
        else:
            return ""
    
    def get_identifier(self) -> str:
        """获取元素标识符"""
        if self.attributes.id:
            return f"#{self.attributes.id}"
        elif self.attributes.name:
            return f"[name='{self.attributes.name}']"
        elif self.attributes.class_name:
            return f".{self.attributes.class_name.split()[0]}"
        else:
            return self.selector
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'selector': self.selector,
            'element_type': self.element_type.value,
            'attributes': self.attributes.__dict__,
            'text_content': self.text_content,
            'bounds': self.bounds.__dict__ if self.bounds else None,
            'states': [state.value for state in self.states],
            'xpath': self.xpath,
            'css_selector': self.css_selector,
            'custom_data': self.custom_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PageElement':
        """从字典创建元素对象"""
        # 处理枚举类型
        if 'element_type' in data:
            data['element_type'] = ElementType(data['element_type'])
        
        if 'states' in data:
            data['states'] = [ElementState(state) for state in data['states']]
        
        # 处理嵌套对象
        if 'attributes' in data and isinstance(data['attributes'], dict):
            data['attributes'] = ElementAttributes(**data['attributes'])
        
        if 'bounds' in data and isinstance(data['bounds'], dict):
            data['bounds'] = ElementBounds(**data['bounds'])
        
        return cls(**data)


@dataclass
class ElementCollection:
    """元素集合"""
    elements: List[PageElement] = field(default_factory=list)
    selector: str = ""
    total_count: int = 0
    
    def __len__(self) -> int:
        return len(self.elements)
    
    def __iter__(self):
        return iter(self.elements)
    
    def __getitem__(self, index: int) -> PageElement:
        return self.elements[index]
    
    def filter_by_type(self, element_type: ElementType) -> 'ElementCollection':
        """按类型过滤"""
        filtered = [elem for elem in self.elements if elem.element_type == element_type]
        return ElementCollection(elements=filtered, selector=self.selector)
    
    def filter_by_state(self, state: ElementState) -> 'ElementCollection':
        """按状态过滤"""
        filtered = [elem for elem in self.elements if elem.has_state(state)]
        return ElementCollection(elements=filtered, selector=self.selector)
    
    def filter_by_text(self, text: str, exact_match: bool = False) -> 'ElementCollection':
        """按文本过滤"""
        if exact_match:
            filtered = [elem for elem in self.elements if elem.get_display_text() == text]
        else:
            filtered = [elem for elem in self.elements if text.lower() in elem.get_display_text().lower()]
        return ElementCollection(elements=filtered, selector=self.selector)
    
    def get_visible_elements(self) -> 'ElementCollection':
        """获取可见元素"""
        return self.filter_by_state(ElementState.VISIBLE)
    
    def get_clickable_elements(self) -> 'ElementCollection':
        """获取可点击元素"""
        filtered = [elem for elem in self.elements if elem.is_clickable()]
        return ElementCollection(elements=filtered, selector=self.selector)