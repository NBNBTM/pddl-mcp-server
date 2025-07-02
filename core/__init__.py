#!/usr/bin/env python3
"""
PDDL MCP 核心模块

提供 PDDL 规划的核心功能，包括任务执行、自然语言处理和计划解释。
基于 FastMCP 框架构建的高性能 PDDL 规划服务。
"""

from .pddl_core import run_mcp_task, generate_plan, get_next_index, extract_task_from_text
from .explain_plan import explain_plan, explain_plan_content
from constants import ServerConstants, DomainConstants

# 版本信息
__version__ = ServerConstants.VERSION
__author__ = ServerConstants.AUTHOR
__framework__ = ServerConstants.FRAMEWORK

# 导出的公共接口
__all__ = [
    'run_mcp_task',
    'generate_plan', 
    'get_next_index',
    'extract_task_from_text',
    'explain_plan',
    'explain_plan_content'
]

# 模块级别的文档
__doc__ = f"""
PDDL MCP 核心模块 ({ServerConstants.FRAMEWORK} 版本)

主要功能：
- run_mcp_task: 执行完整的 PDDL 规划任务
- extract_task_from_text: 从自然语言提取任务信息
- explain_plan: 生成计划的自然语言解释
- generate_plan: 生成 PDDL 计划
- get_next_index: 获取下一个文件索引

使用示例：
    from core import run_mcp_task, extract_task_from_text
    from constants import DomainConstants
    
    # 结构化任务
    task = {{
        "robot": f"{DomainConstants.ROBOT_PREFIX}1", 
        "start": f"{DomainConstants.ROOM_PREFIX}1", 
        "goal": f"{DomainConstants.ROOM_PREFIX}3", 
        "domain": DomainConstants.DEFAULT_DOMAIN
    }}
    result = run_mcp_task(task)
    
    # 自然语言任务
    text = "Move robot r1 from room1 to room3"
    task = extract_task_from_text(text)
    result = run_mcp_task(task)
"""