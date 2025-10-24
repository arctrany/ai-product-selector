"""
运行器接口定义

定义浏览器操作运行器的标准接口
支持复杂的浏览器操作流程编排和执行
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.page_element import PageElement
    from ..exceptions.browser_exceptions import BrowserError
    from .browser_driver import IBrowserDriver
    from .page_analyzer import IPageAnalyzer
    from .paginator import IPaginator
else:
    PageElement = 'PageElement'
    BrowserError = Exception
    IBrowserDriver = 'IBrowserDriver'
    IPageAnalyzer = 'IPageAnalyzer'
    IPaginator = 'IPaginator'


class RunnerStatus(Enum):
    """运行器状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ActionType(Enum):
    """动作类型枚举"""
    NAVIGATE = "navigate"
    CLICK = "click"
    INPUT = "input"
    WAIT = "wait"
    EXTRACT = "extract"
    VALIDATE = "validate"
    SCROLL = "scroll"
    PAGINATE = "paginate"
    CUSTOM = "custom"


class IRunner(ABC):
    """运行器接口 - 定义运行器执行的标准接口"""

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化运行器
        
        Args:
            config: 运行器配置
            
        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行运行器
        
        Args:
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    async def pause(self) -> bool:
        """
        暂停运行器执行
        
        Returns:
            bool: 暂停是否成功
        """
        pass

    @abstractmethod
    async def resume(self) -> bool:
        """
        恢复运行器执行
        
        Returns:
            bool: 恢复是否成功
        """
        pass

    @abstractmethod
    async def cancel(self) -> bool:
        """
        取消运行器执行
        
        Returns:
            bool: 取消是否成功
        """
        pass

    @abstractmethod
    async def get_status(self) -> RunnerStatus:
        """
        获取运行器状态
        
        Returns:
            RunnerStatus: 当前状态
        """
        pass

    @abstractmethod
    async def get_progress(self) -> Dict[str, Any]:
        """
        获取执行进度
        
        Returns:
            Dict[str, Any]: 进度信息
        """
        pass

    @abstractmethod
    async def add_step(self, step: Dict[str, Any]) -> bool:
        """
        添加执行步骤
        
        Args:
            step: 步骤定义
            
        Returns:
            bool: 添加是否成功
        """
        pass

    @abstractmethod
    async def remove_step(self, step_id: str) -> bool:
        """
        移除执行步骤
        
        Args:
            step_id: 步骤ID
            
        Returns:
            bool: 移除是否成功
        """
        pass

    @abstractmethod
    async def validate_runner(self) -> Dict[str, Any]:
        """
        验证运行器配置
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass


class IRunnerStep(ABC):
    """运行器步骤接口 - 定义单个运行器步骤的标准接口"""

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行步骤
        
        Args:
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    async def validate_preconditions(self, context: Dict[str, Any]) -> bool:
        """
        验证前置条件
        
        Args:
            context: 执行上下文
            
        Returns:
            bool: 前置条件是否满足
        """
        pass

    @abstractmethod
    async def validate_postconditions(self, context: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """
        验证后置条件
        
        Args:
            context: 执行上下文
            result: 执行结果
            
        Returns:
            bool: 后置条件是否满足
        """
        pass

    @abstractmethod
    async def rollback(self, context: Dict[str, Any]) -> bool:
        """
        回滚步骤
        
        Args:
            context: 执行上下文
            
        Returns:
            bool: 回滚是否成功
        """
        pass

    @abstractmethod
    def get_step_info(self) -> Dict[str, Any]:
        """
        获取步骤信息
        
        Returns:
            Dict[str, Any]: 步骤信息
        """
        pass


class IRunnerOrchestrator(ABC):
    """运行器编排器接口 - 定义运行器编排和管理的标准接口"""

    @abstractmethod
    async def create_runner(self, runner_definition: Dict[str, Any]) -> str:
        """
        创建运行器
        
        Args:
            runner_definition: 运行器定义
            
        Returns:
            str: 运行器ID
        """
        pass

    @abstractmethod
    async def execute_runner(self, runner_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行运行器
        
        Args:
            runner_id: 运行器ID
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    async def execute_parallel_runners(self, runner_ids: List[str], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        并行执行多个运行器
        
        Args:
            runner_ids: 运行器ID列表
            context: 执行上下文
            
        Returns:
            List[Dict[str, Any]]: 执行结果列表
        """
        pass

    @abstractmethod
    async def execute_sequential_runners(self, runner_ids: List[str], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        顺序执行多个运行器
        
        Args:
            runner_ids: 运行器ID列表
            context: 执行上下文
            
        Returns:
            List[Dict[str, Any]]: 执行结果列表
        """
        pass

    @abstractmethod
    async def get_runner_status(self, runner_id: str) -> RunnerStatus:
        """
        获取运行器状态
        
        Args:
            runner_id: 运行器ID
            
        Returns:
            RunnerStatus: 运行器状态
        """
        pass

    @abstractmethod
    async def pause_runner(self, runner_id: str) -> bool:
        """
        暂停运行器
        
        Args:
            runner_id: 运行器ID
            
        Returns:
            bool: 暂停是否成功
        """
        pass

    @abstractmethod
    async def resume_runner(self, runner_id: str) -> bool:
        """
        恢复运行器
        
        Args:
            runner_id: 运行器ID
            
        Returns:
            bool: 恢复是否成功
        """
        pass

    @abstractmethod
    async def cancel_runner(self, runner_id: str) -> bool:
        """
        取消运行器
        
        Args:
            runner_id: 运行器ID
            
        Returns:
            bool: 取消是否成功
        """
        pass


class IActionExecutor(ABC):
    """动作执行器接口 - 定义具体动作执行的标准接口"""

    @abstractmethod
    async def execute_navigate(self, url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行导航动作
        
        Args:
            url: 目标URL
            options: 导航选项
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    async def execute_click(self, selector: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行点击动作
        
        Args:
            selector: 元素选择器
            options: 点击选项
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    async def execute_input(self, selector: str, text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行输入动作
        
        Args:
            selector: 元素选择器
            text: 输入文本
            options: 输入选项
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    async def execute_wait(self, condition: Dict[str, Any], timeout: int = 10000) -> Dict[str, Any]:
        """
        执行等待动作
        
        Args:
            condition: 等待条件
            timeout: 超时时间(毫秒)
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    async def execute_extract(self, extraction_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据提取动作
        
        Args:
            extraction_config: 提取配置
            
        Returns:
            Dict[str, Any]: 提取结果
        """
        pass

    @abstractmethod
    async def execute_validate(self, validation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行验证动作
        
        Args:
            validation_config: 验证配置
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass

    @abstractmethod
    async def execute_scroll(self, scroll_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行滚动动作
        
        Args:
            scroll_config: 滚动配置
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    async def execute_paginate(self, pagination_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行分页动作
        
        Args:
            pagination_config: 分页配置
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    async def execute_custom(self, action_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行自定义动作
        
        Args:
            action_config: 动作配置
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass


class IRunnerValidator(ABC):
    """运行器验证器接口 - 定义运行器验证的标准接口"""

    @abstractmethod
    async def validate_runner_definition(self, definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证运行器定义
        
        Args:
            definition: 运行器定义
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass

    @abstractmethod
    async def validate_step_sequence(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证步骤序列
        
        Args:
            steps: 步骤列表
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass

    @abstractmethod
    async def validate_dependencies(self, runner_id: str) -> Dict[str, Any]:
        """
        验证运行器依赖
        
        Args:
            runner_id: 运行器ID
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass

    @abstractmethod
    async def validate_resources(self, runner_id: str) -> Dict[str, Any]:
        """
        验证运行器资源
        
        Args:
            runner_id: 运行器ID
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass