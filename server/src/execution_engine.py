import json
import re

class ExecutionEngine:
    """
    执行引擎负责解析并执行由规划器生成的行动计划。
    """
    def __init__(self, tool_registry: dict):
        """
        初始化执行引擎，需要传入一个工具注册表。
        """
        self.tool_registry = tool_registry

    def _get_value_from_path(self, obj, path):
        ""一个辅助函数，用于根据路径字符串（如 'result.id'）从对象中取值"""
        keys = path.split('.')
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key)
            else:
                return None # 路径不匹配
        return obj

    def _resolve_parameters(self, params: dict, step_results: list) -> dict:
        """
        递归地解析参数字典，将所有 "$steps." 引用替换为真实值。
        """
        # 创建一个参数的深拷贝，避免修改原始计划
        resolved_params = json.loads(json.dumps(params))

        # 定义用于匹配 $steps.N.path 的正则表达式
        ref_pattern = re.compile(r"^\$steps\.(\d+)\.(.*)$")

        def _recursive_resolve(current_obj):
            ""递归遍历并替换"""
            if isinstance(current_obj, dict):
                for key, value in current_obj.items():
                    current_obj[key] = _recursive_resolve(value)
            elif isinstance(current_obj, list):
                for i, item in enumerate(current_obj):
                    current_obj[i] = _recursive_resolve(item)
            elif isinstance(current_obj, str):
                match = ref_pattern.match(current_obj)
                if match:
                    step_index = int(match.group(1))
                    result_path = match.group(2)
                    
                    if step_index < len(step_results):
                        source_result = step_results[step_index]
                        real_value = self._get_value_from_path(source_result, result_path)
                        print(f"成功解析引用 '{current_obj}' -> '{real_value}'")
                        return real_value
                    else:
                        print(f"错误：尝试引用一个尚未执行的步骤结果 '{current_obj}'")
                        raise ValueError(f"Invalid step reference: {current_obj}")
            
            return current_obj

        return _recursive_resolve(resolved_params)

    def execute_plan(self, plan: dict):
        """
        执行一个完整的JSON行动计划。
        """
        if 'plan' not in plan or not isinstance(plan['plan'], list):
            print("错误：计划格式不正确，缺少 'plan' 列表。" )
            raise ValueError("Invalid plan format")

        step_results = []
        
        print("--- 开始执行行动计划 ---")
        for i, step in enumerate(plan['plan']):
            print(f"\n>>>>> 正在执行步骤 {i}: {step.get('reasoning', '')}")

            try:
                resolved_params = self._resolve_parameters(step['parameters'], step_results)
                
                tool_name = step['tool_name']
                tool_function = self.tool_registry.get(tool_name)

                if not tool_function:
                    raise ValueError(f"未找到工具 '{tool_name}'")

                result = tool_function(**resolved_params)
                step_results.append(result)
                print(f"<<<<< 步骤 {i} 执行成功，返回结果: {result}")

            except Exception as e:
                print(f"!! 步骤 {i} 执行失败: {e}")
                # 在实际应用中，这里可以触发更复杂的错误处理和重规划逻辑
                raise
        
        print("\n--- 行动计划执行完毕 ---")
        return step_results
