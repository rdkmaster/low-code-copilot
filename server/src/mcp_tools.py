# MCP = Modification and Control Plane
# 这个文件定义了所有能修改或控制低代码平台状态的工具

import random
import string

# 导入自定义异常和页面状态检查工具
from .exceptions import ComponentNotFoundError
from .observation_tools import get_component_details

def _generate_random_id(prefix: str = "comp"):
    """生成一个随机的组件ID"""
    letters = string.ascii_lowercase
    random_str = ''.join(random.choice(letters) for i in range(6))
    return f"{prefix}_{random_str}"

# --- 工具函数定义 ---

def createComponent(parentId: str, componentType: str, properties: dict = None) -> dict:
    """
    在指定的父组件内创建一个新的UI组件。
    """
    # 模拟检查父组件是否存在
    if not get_component_details(parentId):
        raise ComponentNotFoundError(component_id=parentId)
    
    print(f"  [执行] 调用 'createComponent', 在父组件 '{parentId}' 中创建 '{componentType}'...")
    new_id = _generate_random_id(componentType.lower())
    
    # 必须返回一个包含ID的字典，以便后续步骤引用
    return {"id": new_id, "status": "success", "componentType": componentType}

def updateProperty(componentId: str, propertyName: str, propertyValue) -> dict:
    """
    更新一个指定组件的属性。
    """
    # 模拟检查组件是否存在
    if not get_component_details(componentId):
        raise ComponentNotFoundError(component_id=componentId)

    print(f"  [执行] 调用 'updateProperty', 更新组件 '{componentId}' 的属性 '{propertyName}' 为 '{propertyValue}'...")
    return {"id": componentId, "status": "updated"}

def deleteComponent(componentId: str) -> dict:
    """
    删除一个指定的组件。
    """
    # 模拟检查组件是否存在
    if not get_component_details(componentId):
        raise ComponentNotFoundError(component_id=componentId)

    print(f"  [执行] 调用 'deleteComponent', 删除组件 '{componentId}'...")
    return {"id": componentId, "status": "deleted"}

def ask_user_for_clarification(question: str) -> dict:
    """
    当Agent无法继续时，向用户提问以获取更多信息。
    这个工具是特殊的，它会中断执行并向前端返回一个问题。
    """
    print(f"  [执行] 调用 'ask_user_for_clarification', 向用户提问: {question}")
    # 在实际应用中，这将触发一个特殊的返回状态，让前端显示一个提问对话框
    return {"type": "clarification_needed", "question": question}


# --- 工具注册表 ---
# 我们将所有可用的工具函数注册到这个字典中
# 执行引擎将使用这个注册表来动态调度工具

tool_registry = {
    "createComponent": createComponent,
    "updateProperty": updateProperty,
    "deleteComponent": deleteComponent,
    "ask_user_for_clarification": ask_user_for_clarification,
    # 注意：观察工具 (find_components等) 通常由规划器在规划阶段使用，
    # 而不是由执行引擎在执行修改计划时使用，所以我们暂时不把它加到这里。
}
