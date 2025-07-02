#!/usr/bin/env python3
"""
常量和默认配置管理模块

集中管理项目中的所有硬编码常量、默认值和配置参数。
"""

import os
from typing import Dict, Any, List


class PlanningConstants:
    """规划相关常量"""
    
    # 搜索算法配置
    DEFAULT_SEARCH_ALGORITHM = "astar(blind())"
    ALTERNATIVE_ALGORITHMS = [
        "astar(blind())",
        "astar(lmcut())",
        "astar(hmax())",
        "lazy_greedy([ff()], preferred=[ff()])",
        "lama-first"
    ]
    
    # 超时和重试配置
    DEFAULT_TIMEOUT = 300  # 秒
    DEFAULT_MAX_RETRIES = 2
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_BACKOFF_FACTOR = 2.0
    
    # 文件处理配置
    DEFAULT_ERROR_LOG_LENGTH = 500  # 字符
    DEFAULT_FILE_ENCODING = 'utf-8'
    
    # 临时文件名
    SAS_PLAN_FILE = "sas_plan"
    

class FileConstants:
    """文件和路径相关常量"""
    
    # 文件扩展名
    PDDL_EXTENSION = ".pddl"
    TEMPLATE_EXTENSION = ".j2"
    PLAN_EXTENSION = ".txt"
    JSON_EXTENSION = ".json"
    LOG_EXTENSION = ".txt"
    
    # 文件前缀
    PLAN_PREFIX = "plan"
    LOG_PREFIX = "log"
    PROBLEM_PREFIX = "problem"
    
    # 模板文件名
    DOMAIN_TEMPLATE = "domain.pddl"
    PROBLEM_TEMPLATE = "problem_template.pddl.j2"
    
    # 目录名
    TEMPLATES_DIR = "templates"
    OUTPUT_DIR = "output"
    PLAN_DIR = "plan"
    EXPLANATION_DIR = "explanation"
    PDDL_DIR = "pddl"
    TASKS_DIR = "tasks"
    CORE_DIR = "core"
    

class DomainConstants:
    """领域相关常量"""
    
    # 默认领域配置
    DEFAULT_DOMAIN = "delivery"
    DEFAULT_PROBLEM_TYPE = "robot-delivery"
    
    # 实体前缀
    DEFAULT_ROBOT_PREFIX = "r"
    DEFAULT_ROOM_PREFIX = "room"
    DEFAULT_LOCATION_PREFIX = "loc"
    ROBOT_PREFIX = "robot"
    ROOM_PREFIX = "room"
    
    # 动作名称
    MOVE_ACTION = "move"
    
    # 示例实体名称
    EXAMPLE_ROBOTS = ["r1", "r2", "r3"]
    EXAMPLE_ROOMS = ["room1", "room2", "room3"]
    EXAMPLE_LOCATIONS = ["start", "goal", "waypoint"]
    

class ServerConstants:
    """服务器相关常量"""
    
    # 服务器信息
    NAME = "PDDL Planner (FastMCP)"
    VERSION = "2.0.0"
    AUTHOR = "PDDL MCP Team"
    FRAMEWORK = "FastMCP"
    
    # 默认端口配置
    DEFAULT_PORT = 8080
    ALTERNATIVE_PORTS = [8080, 8081, 3000, 5000]
    
    # 网络配置
    DEFAULT_HOST = "localhost"
    DEFAULT_TIMEOUT = 30
    
    # 版本信息
    PROJECT_VERSION = "2.0.0"
    API_VERSION = "v1"
    

class ErrorConstants:
    """错误处理相关常量"""
    
    # 错误类型
    ERROR_TYPES = {
        "CONFIGURATION": "configuration_error",
        "PLANNING": "planning_error",
        "TEMPLATE": "template_error",
        "TIMEOUT": "timeout_error",
        "FILE_NOT_FOUND": "file_not_found",
        "VALIDATION": "validation_error"
    }
    
    # 错误消息模板
    ERROR_MESSAGES = {
        "MISSING_PARAMS": "缺少必需参数: {params}",
        "FILE_NOT_FOUND": "文件不存在: {file_path}",
        "TIMEOUT_ERROR": "操作超时（{timeout}秒）",
        "PLANNING_FAILED": "规划器执行失败: {details}",
        "TEMPLATE_ERROR": "模板处理失败: {error}"
    }
    
    # 错误常量定义
    TIMEOUT = "timeout_error"
    FILE_NOT_FOUND = "file_not_found"
    PLANNING_FAILED = "planning_failed"
    INVALID_INPUT = "invalid_input"
    CONFIGURATION_ERROR = "configuration_error"
    TEMPLATE_ERROR = "template_error"
    
    # 重试配置
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_DELAY = 1.0
    DEFAULT_BACKOFF_FACTOR = 2.0
    

class ValidationConstants:
    """验证相关常量"""
    
    # 必需的任务参数
    REQUIRED_TASK_PARAMS = ['robot', 'start', 'goal', 'domain']
    REQUIRED_FILE_PARAMS = ['domain_path', 'problem_path']
    
    # 文件大小限制（字节）
    MAX_PLAN_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_LOG_FILE_SIZE = 50 * 1024 * 1024   # 50MB
    
    # 字符串长度限制
    MAX_ROBOT_NAME_LENGTH = 50
    MAX_LOCATION_NAME_LENGTH = 100
    MAX_DOMAIN_NAME_LENGTH = 100
    
    # 动作解析相关常量
    MIN_ACTION_PARTS = 4  # move 动作最少需要4个部分：动作名、机器人、起始位置、目标位置
    
    # 命令行参数数量
    EXPECTED_CLI_ARGS = 3  # 脚本名 + 2个参数
    

class PerformanceConstants:
    """性能相关常量"""
    
    # 缓存配置
    CACHE_SIZE = 100
    CACHE_TTL = 3600  # 秒
    
    # 并发配置
    MAX_CONCURRENT_TASKS = 5
    THREAD_POOL_SIZE = 4
    
    # 内存限制
    MAX_MEMORY_USAGE = 512 * 1024 * 1024  # 512MB
    

class LoggingConstants:
    """日志相关常量"""
    
    # 日志级别
    DEFAULT_LOG_LEVEL = "INFO"
    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    # 日志格式
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    
    # 日志文件配置
    LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT = 5
    
    # 新增的日志常量
    DEFAULT_LEVEL = "INFO"
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    SEPARATOR = "=" * 50
    
    # 日志文件配置
    DEFAULT_LOG_FILE = "pddl_mcp.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    

class EnvironmentConstants:
    """环境变量相关常量"""
    
    # 环境变量名称
    ENV_VARS = {
        "FAST_DOWNWARD_PATH": "FAST_DOWNWARD_PATH",
        "PDDL_DOMAIN_PATH": "PDDL_DOMAIN_PATH",
        "LOG_LEVEL": "LOG_LEVEL",
        "SERVER_PORT": "SERVER_PORT",
        "MAX_PLANNING_TIME": "MAX_PLANNING_TIME",
        "PYTHONPATH": "PYTHONPATH"
    }
    
    # 默认环境变量值
    DEFAULT_ENV_VALUES = {
        "LOG_LEVEL": LoggingConstants.DEFAULT_LOG_LEVEL,
        "SERVER_PORT": str(ServerConstants.DEFAULT_PORT),
        "MAX_PLANNING_TIME": str(PlanningConstants.DEFAULT_TIMEOUT)
    }
    

def get_constant(category: str, name: str, default: Any = None) -> Any:
    """获取常量值
    
    Args:
        category: 常量类别（如 'planning', 'file', 'domain' 等）
        name: 常量名称
        default: 默认值
        
    Returns:
        常量值
    """
    category_map = {
        'planning': PlanningConstants,
        'file': FileConstants,
        'domain': DomainConstants,
        'server': ServerConstants,
        'error': ErrorConstants,
        'validation': ValidationConstants,
        'performance': PerformanceConstants,
        'logging': LoggingConstants,
        'environment': EnvironmentConstants
    }
    
    category_class = category_map.get(category.lower())
    if category_class is None:
        return default
        
    return getattr(category_class, name.upper(), default)


def get_env_with_default(env_var: str, default: Any = None) -> str:
    """获取环境变量值，如果不存在则返回默认值
    
    Args:
        env_var: 环境变量名
        default: 默认值
        
    Returns:
        环境变量值或默认值
    """
    return os.environ.get(env_var, default or EnvironmentConstants.DEFAULT_ENV_VALUES.get(env_var, ""))


def get_all_constants() -> Dict[str, Dict[str, Any]]:
    """获取所有常量的字典表示
    
    Returns:
        包含所有常量的嵌套字典
    """
    return {
        'planning': {
            attr: getattr(PlanningConstants, attr)
            for attr in dir(PlanningConstants)
            if not attr.startswith('_')
        },
        'file': {
            attr: getattr(FileConstants, attr)
            for attr in dir(FileConstants)
            if not attr.startswith('_')
        },
        'domain': {
            attr: getattr(DomainConstants, attr)
            for attr in dir(DomainConstants)
            if not attr.startswith('_')
        },
        'server': {
            attr: getattr(ServerConstants, attr)
            for attr in dir(ServerConstants)
            if not attr.startswith('_')
        },
        'error': {
            attr: getattr(ErrorConstants, attr)
            for attr in dir(ErrorConstants)
            if not attr.startswith('_')
        },
        'validation': {
            attr: getattr(ValidationConstants, attr)
            for attr in dir(ValidationConstants)
            if not attr.startswith('_')
        },
        'performance': {
            attr: getattr(PerformanceConstants, attr)
            for attr in dir(PerformanceConstants)
            if not attr.startswith('_')
        },
        'logging': {
            attr: getattr(LoggingConstants, attr)
            for attr in dir(LoggingConstants)
            if not attr.startswith('_')
        },
        'environment': {
            attr: getattr(EnvironmentConstants, attr)
            for attr in dir(EnvironmentConstants)
            if not attr.startswith('_')
        }
    }