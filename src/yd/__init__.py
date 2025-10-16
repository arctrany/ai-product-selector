# 影刀RPA模块初始化文件
# 用于支持模块间的相对导入

# 导入主要模块，使其可以被其他模块访问
try:
    from . import seefar_test
    __all__ = ['seefar_test']
except ImportError:
    # 如果相对导入失败，尝试直接导入
    try:
        import seefar_test
        __all__ = ['seefar_test']
    except ImportError:
        __all__ = []