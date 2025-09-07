# -- exceptions.py --

class MCPToolError(Exception):
    """所有MCP工具错误的基类"""
    pass

class ComponentNotFoundError(MCPToolError):
    """当根据ID或条件找不到组件时抛出"""
    def __init__(self, component_id=None, filters=None):
        if component_id:
            super().__init__(f"执行失败：未能在画布上找到ID为 '{component_id}' 的组件。")
        else:
            super().__init__(f"执行失败：根据筛选条件 {filters} 未找到任何组件。")

class InvalidParameterError(MCPToolError):
    """当工具收到的参数无效或缺失时抛出"""
    def __init__(self, tool_name, message):
        super().__init__(f"执行失败：调用工具 '{tool_name}' 时参数无效: {message}")
