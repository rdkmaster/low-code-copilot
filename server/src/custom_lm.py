import dspy
from openai import OpenAI
from typing import List, Union

class CustomLM(dspy.BaseLM):
    def __init__(self, api_base: str, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(model=model)
        self.model = model
        self.client = OpenAI(
            base_url=api_base,
            api_key=api_key
        )
    
    def basic_generate(self, prompt: Union[str, List], temperature: float = 0.7, **kwargs) -> List[str]:
        """实现基础生成方法"""
        try:
            if isinstance(prompt, str):
                messages = [{"role": "user", "content": prompt}]
            elif isinstance(prompt, list):
                messages = prompt
            else:
                raise ValueError("prompt必须是字符串或列表类型")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                **kwargs
            )
            return [response.choices[0].message.content]
        except Exception as e:
            print(f"API调用出错: {e}")
            return [""]
    
    def __call__(self, prompt: Union[str, List] = None, temperature: float = 0.7, messages = None, **kwargs) -> List[str]:
        """实现调用方法，支持prompt和messages两种输入方式"""
        if messages is not None:
            return self.basic_generate(messages, temperature, **kwargs)
        elif prompt is not None:
            return self.basic_generate(prompt, temperature, **kwargs)
        else:
            raise ValueError("必须提供prompt或messages参数") 