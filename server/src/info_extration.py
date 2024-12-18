# -*- coding: utf-8 -*-

from custom_lm import CustomLM
import dspy

# 直接使用导入的 CustomLM
lm = CustomLM(
    api_base="https://xiaoai.plus/v1",
    api_key="sk-yhJhB5JgplmHZHXghuCbAbxr3GUzotlKd4MffZedhxVVNAZX"
)
dspy.configure(lm=lm)

class ExtractInfo(dspy.Signature):
    """Extract structured information from text."""

    text: str = dspy.InputField()
    title: str = dspy.OutputField()
    headings: list[str] = dspy.OutputField()
    entities: list[dict[str, str]] = dspy.OutputField(desc="实体及其元数据的列表")

module = dspy.Predict(ExtractInfo)

text = "2024年12月18日，李华带着他的宠物狗“毛球”来到北京的天安门广场，准备参加由“阳光公益组织”举办的慈善义卖活动。活动从上午10点持续到下午3点，吸引了许多人参加。李华买了一本《Python编程入门》，售价50元，并捐赠了一些旧衣物。随后，他前往星巴克点了一杯拿铁咖啡，准备整理下午的工作计划。他计划在明天与张强一起去上海参加一个科技展览，该展览由“未来科技协会”主办，将展示最新的AI技术成果。"
response = module(text=text)

print(response.title)
print('---------------------------------------')
print(response.headings)
print('---------------------------------------')
print(response.entities)

