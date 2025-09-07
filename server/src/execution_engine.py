import json
import re

from .planner import Planner
from .exceptions import MCPToolError
from .observation_tools import get_page_outline
from .page_state import summarize_page_state

# “自我修正”的思考框架 (Re-Planning Meta-Prompt)
REPLANNING_PROMPT_TEMPLATE = '''
# 角色扮演

你是一位经验丰富的软件调试专家和解决问题的能手。你的一个自动化代理在执行一个计划时遇到了错误。现在, 你需要分析这次失败，并制定一个全新的、修正后的计划来达成最初的用户目标。

# 事故报告 (Failure Context)

以下是关于这次执行失败的详细报告：

## 1. 用户的原始目标
{original_goal}

## 2. 完整的原始计划
```json
{original_plan}
```

## 3. 已成功执行的步骤
```json
{succeeded_steps}
```

## 4. 失败的步骤详情
- 步骤索引: {failed_step_index}
- 失败的步骤:
```json
{failed_step}
```

## 5. 具体的错误信息
"{error_message}"

# 当前快照 (Updated Awareness)

在上述步骤执行后（包括失败的步骤之前所有成功的步骤），低代码画布的最新状态如下。这是你决策的主要依据：

{current_page_state}

# 可用工具清单

你可以使用以下工具来构建新的计划：
{tools_description}

# 新的任务指令 (The New Task)

你的任务是：
1.  **分析**：仔细分析上述“事故报告”和“当前快照”。理解为什么会发生错误。
2.  **规划**：基于你的分析，生成一个全新的、修正后的行动计划。这个新计划的目标是绕过或解决当前遇到的问题，并最终达成用户的“原始目标”。
3.  **策略**：新计划应该从你认为最合适的步骤开始。它可以是全新的，也可以是利用之前成功步骤的结果。例如，如果错误是“组件未找到”，一个好的策略可能是先用 `find_components` 工具来查找类似组件，或者用 `ask_user_for_clarification` 工具来询问用户。

# 输出契约

你必须严格按照以下JSON格式返回你的新计划，不要包含任何额外的解释或注释。

{
  "plan": [
    {
      "thought": "在这里写下你关于这一步的思考过程。",
      "tool_name": "tool_name_1",
      "parameters": {{...}}
    }
  ]
}
'''

class ExecutionEngine:
    """
    执行引擎负责解析并执行由规划器生成的行动计划。
    增加了错误处理和重规划（自我修正）的能力。
    """
    def __init__(self, tool_registry: dict, planner: Planner, max_retries: int = 2):
        """
        初始化执行引擎。
        :param tool_registry: 工具注册表。
        :param planner: 规划器实例，用于重规划。
        :param max_retries: 最大重规划次数。
        """
        self.tool_registry = tool_registry
        self.planner = planner
        self.max_retries = max_retries

    def _get_value_from_path(self, obj, path):
        """一个辅助函数，用于根据路径字符串（如 'result.id' 或 'result.0.name'）从对象中取值"""
        keys = path.split('.')
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key)
            elif isinstance(obj, list) and key.isdigit():
                try:
                    obj = obj[int(key)]
                except IndexError:
                    return None # 索引越界
            else:
                return None # 路径不匹配或对象类型不支持
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
            """递归遍历并替换"""
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
                        raise ValueError(f"无效的步骤引用: {current_obj}")
            return current_obj

        return _recursive_resolve(resolved_params)

    def _replan(self, failure_context: dict) -> dict | None:
        ""根据失败上下文进行重规划。"""
        print("\n--- 正在调用规划器进行自我修正 ---")
        current_state_raw = get_page_outline()
        current_state_summary = summarize_page_state(current_state_raw)

        prompt = REPLANNING_PROMPT_TEMPLATE.format(
            original_goal=failure_context['original_goal'],
            original_plan=json.dumps(failure_context['original_plan'], indent=2, ensure_ascii=False),
            succeeded_steps=json.dumps(failure_context['succeeded_steps'], indent=2, ensure_ascii=False),
            failed_step_index=failure_context['failed_step_index'],
            failed_step=json.dumps(failure_context['failed_step'], indent=2, ensure_ascii=False),
            error_message=failure_context['error_message'],
            current_page_state=current_state_summary,
            tools_description=self.planner.get_tools_description()
        )

        new_plan = self.planner.generate_plan_from_prompt(prompt)
        if new_plan:
            print("--- 已生成新的修正计划 ---")
            print(json.dumps(new_plan, indent=2, ensure_ascii=False))
        else:
            print("--- 重规划失败，无法生成新计划 ---")
        return new_plan

    def execute_plan(self, original_goal: str, plan: dict):
        """
        执行一个完整的JSON行动计划，包含重试逻辑。
        """
        current_plan = plan
        retries = 0

        while retries <= self.max_retries:
            step_results = []
            succeeded_steps = []
            execution_failed = False

            print(f"--- 开始执行行动计划 (尝试次数 {retries + 1}) ---")
            for i, step in enumerate(current_plan.get('plan', [])):
                try:
                    print(f"\n>>>>> 正在执行步骤 {i}: {step.get('tool_name', 'N/A')}")
                    print(f"思考: {step.get('reasoning', '无')}")

                    resolved_params = self._resolve_parameters(step['parameters'], step_results)
                    tool_name = step['tool_name']
                    tool_function = self.tool_registry.get(tool_name)

                    if not tool_function:
                        raise MCPToolError(f"工具 '{tool_name}' 在注册表中未找到。")

                    result = tool_function(**resolved_params)
                    step_results.append(result)
                    succeeded_steps.append(step)
                    print(f"<<<<< 步骤 {i} 执行成功，返回结果: {result}")

                    # 如果是需要用户澄清的特殊工具，则中断执行并返回结果
                    if result and result.get("type") == "clarification_needed":
                        print("--- 执行中断：需要用户澄清。---")
                        return result

                except MCPToolError as e:
                    print(f"!! 步骤 {i} 执行失败: {e}")
                    failure_context = {
                        "original_goal": original_goal,
                        "original_plan": current_plan,
                        "succeeded_steps": succeeded_steps,
                        "failed_step_index": i,
                        "failed_step": step,
                        "error_message": str(e)
                    }
                    new_plan = self._replan(failure_context)
                    if new_plan:
                        current_plan = new_plan
                        retries += 1
                        execution_failed = True
                        break # 中断当前计划的for循环，开始外层while循环的新尝试
                    else:
                        return {"type": "error", "message": "执行失败且重规划失败。"}
                except Exception as e:
                    return {"type": "error", "message": f"发生意外的严重错误: {e}"}

            if not execution_failed:
                print("\n--- 行动计划执行完毕 ---")
                return {"type": "execution_success", "data": step_results}

        return {"type": "error", "message": f"执行失败，已达到最大重试次数 ({self.max_retries})。"}
