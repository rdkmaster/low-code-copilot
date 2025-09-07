import json
import litellm

# 我们把上一讲定义的观察工具和这一讲的状态摘要工具放在一起
from .page_state import summarize_page_state

class Planner:
    def __init__(self):
        # 在实际项目中，工具定义应该从配置文件中加载
        self.tools_definition = self._load_tools_definition()

    def _load_tools_definition(self) -> str:
        """加载并格式化可用的工具清单。"""
        # 为简化起见，我们在这里直接硬编码
        tools = [
            "`find_components(filters: array)`: 根据一个或多个属性条件，查找页面上所有符合条件的组件列表。",
            "`createComponent(parentId: string, componentType: string, properties: object)`: 在指定的父容器内，创建一个新的组件。",
            "`updateProperty(componentId: string, propertyName: string, propertyValue: any)`: 更新一个指定组件的某个属性。",
            "`deleteComponent(componentId: string)`: 删除一个指定的组件。",
            "`ask_user_for_clarification(question: string)`: 当无法继续时，向用户提问以获取澄清信息。"
        ]
        return "\n".join([f"- {tool}" for tool in tools])

    def get_tools_description(self) -> str:
        """返回格式化的工具描述字符串。"""
        return self.tools_definition

    def _build_meta_prompt(self, goal: str, state_summary: str) -> str:
        """
        动态拼装“终极元提示”。这正是我们设计的核心所在！
        """
        # 1. 角色扮演 (Role-Playing)
        role_prompt = "你是一位资深的低代码应用架构师。你的任务是分析用户的需求，并将其分解为一系列清晰、有序、可执行的步骤。"

        # 2. 最终目标 (The Goal)
        goal_prompt = f"用户的最终目标是: \"{goal}\""

        # 3. 环境感知 (Environmental Awareness)
        env_prompt = f"这是当前页面的结构摘要:\n```markdown\n{state_summary}\n```"

        # 4. 可用工具 (Available Tools)
        tools_prompt = f"你可以使用以下工具来操作页面:\n{self.tools_definition}"

        # 5. 输出契约与行动纲领 (Output Contract & Principles)
        contract_prompt = '''
你的输出必须是一个严格的JSON格式对象，结构如下:
{
  "plan": [
    {
      "step": <步骤序号>,
      "reasoning": "<你对这一步的思考过程>",
      "tool_name": "<要调用的工具名>",
      "parameters": { <调用工具所需的参数> }
    }
  ]
}

你必须遵守以下行动纲领:
1.  **ReAct原则**: 在决定使用某个工具前，必须先在`reasoning`字段中清晰地写下你的思考过程。
2.  **观察优先**: 在执行任何“修改”类工具（如`createComponent`, `updateProperty`）之前，如果需要，应先使用“观察”类工具（如`find_components`）来核实当前状态。
3.  **上下文引用**: 如果一个步骤需要使用前面步骤的执行结果（比如一个新创建组件的ID），你必须使用特殊语法`$steps.N.result.path`来引用。例如，`"$steps.0.result.id"`代表引用第0步执行结果中的id字段。
4.  **经济原则**: 尽量用最少的步骤完成目标。
'''
        # 将所有部分拼装成一个完整的、巨大的字符串
        full_prompt = f"{role_prompt}\n\n{goal_prompt}\n\n{env_prompt}\n\n{tools_prompt}\n\n{contract_prompt}"
        return full_prompt

    def generate_plan_from_prompt(self, prompt: str) -> dict | None:
        """直接从一个完整的提示词生成计划，用于重规划。"""
        try:
            response = litellm.completion(
                model="gpt-4o",
                messages=[{"content": prompt, "role": "user"}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            plan_text = response.choices[0].message.content
            return json.loads(plan_text)
        except json.JSONDecodeError as e:
            print(f"LLM在重规划时返回的计划不是有效的JSON格式: {e}")
            return None
        except Exception as e:
            print(f"调用LLM进行重规划时出错: {e}")
            return None

    def generate_plan(self, goal: str, page_state: dict) -> dict | None:
        """
        生成行动计划的核心方法。
        """
        # 1. 获取对LLM友好的环境信息
        state_summary = summarize_page_state(page_state)
        
        # 2. 拼装元提示
        meta_prompt = self._build_meta_prompt(goal, state_summary)
        
        # 3. 调用LLM API
        return self.generate_plan_from_prompt(meta_prompt)
