import json
import re
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.models.testcase import SCENARIO_TYPES, is_valid_scenario_type


def _get_type_specific_instruction(req_type):
    """
    Get specific instructions based on the requirement type.
    """
    instructions = {
        "功能测试": "重点关注业务逻辑的正确性。必须严格遵循【MC/DC覆盖】和【判定覆盖】标准：详细分析需求中的逻辑判定（Decision）与原子条件（Condition），设计充分的用例组合以确保每个判定都能取到真/假值，并且每个条件都能在其他条件不变的情况下独立影响判定结果。",
        "边界测试": "",
        "接口测试": "",
        "数据处理测试": "",
        "安全性测试": "",
        "可靠性测试": "",
        "强度测试": "",
        "性能测试": "",
        "容量测试": "重点关注系统的【最大服务能力边界】。必须通过阶梯式加压确定系统在满足SLA（如响应时间 < 3s、错误率 < 0.1%）的前提下，所能承载的最大并发用户数、TPS以及数据库单表最大有效数据量。需记录性能拐点，即资源利用率急剧上升而吞吐量增速放缓的关键点。",
        "余量测试": "重点关注系统的【安全缓冲空间】与【抗风险韧性】。在已知最大容量的基础上，验证系统在目标负载（通常为预期峰值的1.2倍）下的资源剩余情况。必须评估CPU、内存、I/O及带宽的空闲百分比，确保在单点故障或瞬时突发流量下，系统具备足够的冗余度以避免雪崩效应。",
    }
    return instructions.get(req_type, "重点关注业务功能的实现是否符合需求描述。")


def _build_system_prompt(req_type):
    """
    Build the system prompt with type-specific instructions.
    """
    type_instruction = _get_type_specific_instruction(req_type)

    scenario_types = "、".join(f"`{item}`" for item in SCENARIO_TYPES)

    return f"""你是一个专业的软件测试工程师。你的任务是根据给定的软件需求描述，编写对应的【{req_type}】用例。

{type_instruction}

请输出纯粹的 JSON 格式数据，不要包含 Markdown 代码块标记（如 ```json ... ```）。
输出应该是一个 JSON 列表，列表中的每个元素代表一个测试用例。

**重要要求：每个测试用例必须包含一个简洁、概括性的标题 `title`。**
1. `title` 用于概括该条用例验证的核心场景/条件/期望结果。
2. 必须是自然语言短句（建议中文），不要包含编号前缀（如"用例001"）。
3. 建议控制在 6~30 个字符内，避免把整段需求原文粘贴进来。

**重要要求：每个测试用例必须包含至少 3 个测试步骤。请详细拆解测试过程，例如包括初始化设置、中间状态检查、触发动作、最终结果验证等。**

**重要要求：每个测试用例必须包含用例场景字段 `scenario_type`。**
1. `scenario_type` 只能从以下五个值中选择一个：{scenario_types}。
2. 请结合需求内容，尽量覆盖所有适用的场景类别，包括正常流程、边界条件、异常场景、组合场景和回归测试。
3. 不要为了凑齐五类而生成与需求无关或不合理的用例；不适用的类别可以不生成。
4. 每条用例只能归属于一个最主要的场景类别。

**核心规则：变量识别与命名**
在编写 `step_desc`（测试步骤描述）时，**严禁**只使用纯自然语言描述。
你**必须**识别出需求中的关键数据项，并将其转化为 **[变量名] = [值]** 的形式。
1. 如果需求描述中已包含英文变量名（如 `真实风向有效值`），直接使用该变量名。
2. 如果需求描述中只有中文名称（如 `航向有效值`），请根据含义生成合理的英文变量名（如 `WindDirectionTrueFMSSideIsValid`）。
3. 格式要求：`中文描述 (变量名 = 值)`。

**错误示例**：
"step_desc": "打开 PFD 菜单"

**正确示例**：
"step_desc": "设置PFD菜单开启，PFD菜单标识PFDActiveMenu = 1"

JSON 对象结构如下：
{{
"test_case_id": "TC-[需求ID]-[用例ID]",
"title": "概括该条用例的标题",
"test_target_desc": "测试目标描述",
"requirement_id": "REG-[需求ID]",
"test_case_type": "{req_type}",
"scenario_type": "正常流程用例",
"verify_method": "TESTING",
"test_steps": [
{{
  "step_desc": "加载输入接口默认值",
  "expectation": "加载成功"
}},
{{
  "step_desc": "初始化变量。例如：设置活门全关信号计数 (ValveCloseCount = 81)",
  "expectation": "确认初始化成功"
}},
{{
  "step_desc": "执行操作。例如：触发信号采集 (SignalSample = 100)",
  "expectation": "确认操作被接受"
}},
{{
  "step_desc": "验证结果。例如：检查活门全关信号状态 (ValveCloseStatus == Closed)",
  "expectation": "确认符合预期结果"
}}
]
}}

其中 `[需求ID]` 替换为当前需求的 ID，`[用例ID]` 为自增编号（例如 001, 002）。
请确保生成的内容严格遵循上述结构，并确保 JSON 格式合法。
"""


class TestCaseGenerator:
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def generate_test_cases(self, requirement_content, item_id, item_title, req_type="功能测试", temperature=0.1, project_background=None, module_info=None):
        """
        Generate test cases from requirements using OpenAI API.
        
        Args:
            requirement_content (str): The content of the requirement.
            item_id (str): The ID of the requirement.
            item_title (str): The title of the requirement.
            req_type (str): The type of the test case (default: "功能测试").
            temperature (float): The temperature for the AI model (default: 0.1).
            project_background (str, optional): The background information of the project.
            module_info (str, optional): The module information that the requirement belongs to.
            
        Returns:
            list: A list of generated test case dictionaries, or None if failed.
        """
        system_prompt = _build_system_prompt(req_type)
        
        user_prompt = f"""需求编号：{item_id}
需求标题：{item_title}
需求类型：{req_type}

"""
        
        if project_background:
            user_prompt += f"项目背景：{project_background}\n\n"
        
        if module_info:
            user_prompt += f"需求所属模块：{module_info}\n\n"
        
        user_prompt += f"请根据以下软件需求内容生成测试用例：\n\n{requirement_content}\n"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(role="system", content=system_prompt),
                    ChatCompletionUserMessageParam(role="user", content=user_prompt),
                ],
                temperature=temperature,
                top_p=0.8,
            )
            content = response.choices[0].message.content
            clean_content = content.strip()
            
            clean_content = re.sub(r'<thinking>.*?</thinking>', '', clean_content, flags=re.DOTALL)
            
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            elif clean_content.startswith("```"):
                clean_content = clean_content[3:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]
                
            result = json.loads(clean_content.strip())
            
            # Ensure list format and update type
            final_result = []
            if isinstance(result, list):
                for tc in result:
                    if not isinstance(tc, dict) or not is_valid_scenario_type(
                        tc.get("scenario_type")
                    ):
                        raise ValueError("测试用例缺少合法的 scenario_type")
                    tc['test_case_type'] = req_type
                    final_result.append(tc)
            elif isinstance(result, dict):
                if not is_valid_scenario_type(result.get("scenario_type")):
                    raise ValueError("测试用例缺少合法的 scenario_type")
                result['test_case_type'] = req_type
                final_result.append(result)
            else:
                raise ValueError("测试用例响应必须是 JSON 对象或列表")
                 
            return final_result
        except json.JSONDecodeError:
            print(f"解析条目 {item_id} 的 JSON 响应失败")
            return None
        except Exception as e:
            print(f"调用 API 时出错: {e}")
            return None
