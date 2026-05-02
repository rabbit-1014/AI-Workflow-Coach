from typing import List

from pydantic import BaseModel, Field


class RouteStep(BaseModel):
    step_name: str = Field(description="步骤名称")
    step_goal: str = Field(description="这一步要做什么")
    primary_tool: str = Field(description="首选工具与功能")
    backup_tool: str = Field(description="备选工具与原因")
    suggested_input: str = Field(description="建议输入")
    expected_output: str = Field(description="预期产出")
    execution_tip: str = Field(description="执行提醒")
    ready_check: str = Field(description="进入下一步前的最低通过标准")


class RouteOutput(BaseModel):
    task_summary: str = Field(description="对用户任务的简要理解")
    route_type: str = Field(description="路线类型，例如完整路线或通用起步路线")
    steps: List[RouteStep] = Field(description="完整路线步骤列表，第一版通常为 5 到 7 步")


class BlockageOutput(BaseModel):
    why_stuck: str = Field(description="为什么容易卡在这里")
    substeps: List[str] = Field(description="把当前步骤拆得更细的执行子步骤")
    simple_input: str = Field(description="更简单、可直接参考的输入示例")
    alternative_tool: str = Field(description="替代工具或替代做法")
    done_check: str = Field(description="这一步完成的判断标准")