
INTENT_SCHEMAS = {
    "createComponent": {
        "params": {
            "componentType": {
                "required": True,
                "prompt": "好的，您想创建什么类型的组件呢？（例如：按钮、输入框、表单）"
            },
            "parentId": {
                "required": True,
                "prompt": "了解。请问您想把这个新组件添加到哪个容器里呢？（您可以告诉我容器的名称或ID）"
            },
            "text": {
                "required": False,
                "prompt": "需不需要给它加上一些文字？"
            },
            "color": {
                "required": False,
                "prompt": "您希望它是什么颜色的？"
            }
        }
    },
    "updateProperty": {
        "params": {
            "componentId": {
                "required": True,
                "prompt": "好的，您想修改哪个组件的属性？（请提供组件ID）"
            },
            "propertyName": {
                "required": True,
                "prompt": "您想修改哪个属性？（例如：text, color）"
            },
            "propertyValue": {
                "required": True,
                "prompt": "您想把这个属性修改成什么值？"
            }
        }
    }
    # 可以在这里添加更多意图的模板
}
