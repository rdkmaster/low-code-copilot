from custom_lm import CustomLM
import dspy
from typing import Literal

# 直接使用导入的 CustomLM
lm = CustomLM(
    api_base="https://xiaoai.plus/v1",
    api_key="sk-yhJhB5JgplmHZHXghuCbAbxr3GUzotlKd4MffZedhxVVNAZX"
)
dspy.configure(lm=lm)

class Classify(dspy.Signature):
    """对句子进行分类。"""

    sentence: str = dspy.InputField(desc="输入句子")
    sentiment: Literal['科技', '教育', '健康', '建议', '其他'] = dspy.OutputField(
        desc="只输出句子类型，并且必须是 '科技'、'教育'、'健康'、'娱乐'或'其他' 之一"
    )
    confidence: float = dspy.OutputField(desc="分类的置信度 (0-1)")

# 创建分类器
classify = dspy.Predict(Classify)

res = classify(sentence="最新的AI模型已经可以生成非常逼真的图片了。")
print(res)
res = classify(sentence="学校刚刚宣布了寒假的时间安排。")
print(res)
res = classify(sentence="每天坚持运动，身体会更健康。")
print(res)
res = classify(sentence="最近上映的电影评价都不错，周末去看。")
print(res)
