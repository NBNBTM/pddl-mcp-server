#!/usr/bin/env python3
"""
配置管理模块

统一管理项目的所有配置项，包括路径、环境变量和默认设置。
集成常量管理系统，提供灵活的配置选项。
"""

import os
from pathlib import Path
from typing import Dict, Optional, List, Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from constants import (
    PlanningConstants, FileConstants, DomainConstants, 
    ServerConstants, EnvironmentConstants, get_env_with_default
)


class Config:
    """项目配置管理类"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_config()
            self._initialized = True
    
    def _load_config(self):
        """加载配置"""
        # 加载环境变量文件
        if load_dotenv:
            env_path = self.get_project_root() / '.env'
            if env_path.exists():
                load_dotenv(env_path)
    
    @classmethod
    def get_project_root(cls) -> Path:
        """获取项目根目录"""
        return Path(__file__).parent.absolute()
    
    @classmethod
    def get_paths(cls) -> Dict[str, Path]:
        """获取所有重要路径"""
        root = cls.get_project_root()
        return {
            'root': root,
            'core': root / 'core',
            'templates': root / 'templates',
            'output': root / 'output',
            'output_plan': root / 'output' / 'plan',
            'output_explanation': root / 'output' / 'explanation',
            'output_pddl': root / 'output' / 'pddl',
            'tasks': root / 'tasks',
            'domain': root / 'templates' / 'domain.pddl',
            'problem_template': root / 'templates' / 'problem_template.pddl.j2'
        }
    
    @classmethod
    def get_env_config(cls) -> Dict[str, str]:
        """获取环境变量配置"""
        paths = cls.get_paths()
        fast_downward_path = get_env_with_default('FAST_DOWNWARD_PATH', 'fast-downward.py')
        return {
            'PDDL_DOMAIN_PATH': get_env_with_default('PDDL_DOMAIN_PATH', str(paths['domain'])),
            'FAST_DOWNWARD_PATH': fast_downward_path,
            'fast_downward_path': fast_downward_path,  # 兼容性别名
            'PYTHONPATH': get_env_with_default('PYTHONPATH', ''),
            'LOG_LEVEL': get_env_with_default('LOG_LEVEL'),
            'SERVER_PORT': get_env_with_default('SERVER_PORT'),
            'MAX_PLANNING_TIME': get_env_with_default('MAX_PLANNING_TIME')
        }
    
    @classmethod
    def ensure_directories(cls) -> None:
        """确保所有必要的目录存在"""
        paths = cls.get_paths()
        required_dirs = [
            paths['output'],
            paths['output_plan'],
            paths['output_explanation'],
            paths['output_pddl']
        ]
        
        for dir_path in required_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """验证配置的有效性"""
        paths = cls.get_paths()
        env_config = cls.get_env_config()
        
        validation_results = {
            'domain_file_exists': Path(env_config['PDDL_DOMAIN_PATH']).exists(),
            'template_file_exists': paths['problem_template'].exists(),
            'core_dir_exists': paths['core'].exists(),
            'output_dir_exists': paths['output'].exists()
        }
        
        return validation_results
    
    @classmethod
    def get_default_task_format(cls) -> Dict[str, str]:
        """获取默认任务格式"""
        return {
            'domain': DomainConstants.DEFAULT_DOMAIN,
            'problem': DomainConstants.DEFAULT_PROBLEM_TYPE,
            'robot_prefix': DomainConstants.DEFAULT_ROBOT_PREFIX,
            'room_prefix': DomainConstants.DEFAULT_ROOM_PREFIX
        }
    
    @classmethod
    def get_planning_config(cls) -> Dict[str, Any]:
        """获取规划相关配置"""
        return {
            'search_algorithm': get_env_with_default('SEARCH_ALGORITHM', PlanningConstants.DEFAULT_SEARCH_ALGORITHM),
            'timeout': int(get_env_with_default('MAX_PLANNING_TIME', str(PlanningConstants.DEFAULT_TIMEOUT))),
            'max_retries': int(get_env_with_default('MAX_RETRIES', str(PlanningConstants.DEFAULT_MAX_RETRIES))),
            'retry_delay': float(get_env_with_default('RETRY_DELAY', str(PlanningConstants.DEFAULT_RETRY_DELAY))),
            'backoff_factor': float(get_env_with_default('BACKOFF_FACTOR', str(PlanningConstants.DEFAULT_BACKOFF_FACTOR))),
            'error_log_length': int(get_env_with_default('ERROR_LOG_LENGTH', str(PlanningConstants.DEFAULT_ERROR_LOG_LENGTH)))
        }
    
    @classmethod
    def get_server_config(cls) -> Dict[str, Any]:
        """获取服务器相关配置"""
        return {
            'port': int(get_env_with_default('SERVER_PORT', str(ServerConstants.DEFAULT_PORT))),
            'host': get_env_with_default('SERVER_HOST', ServerConstants.DEFAULT_HOST),
            'timeout': int(get_env_with_default('SERVER_TIMEOUT', str(ServerConstants.DEFAULT_TIMEOUT))),
            'version': ServerConstants.PROJECT_VERSION,
            'api_version': ServerConstants.API_VERSION
        }
    
    @classmethod
    def get_file_config(cls) -> Dict[str, str]:
        """获取文件相关配置"""
        return {
            'plan_prefix': FileConstants.PLAN_PREFIX,
            'log_prefix': FileConstants.LOG_PREFIX,
            'plan_extension': FileConstants.PLAN_EXTENSION,
            'log_extension': FileConstants.LOG_EXTENSION,
            'encoding': PlanningConstants.DEFAULT_FILE_ENCODING,
            'sas_plan_file': PlanningConstants.SAS_PLAN_FILE
        }


# 全局配置实例
config = Config()


# 便捷函数
def get_project_root() -> Path:
    """获取项目根目录"""
    return Config.get_project_root()


def get_paths() -> Dict[str, Path]:
    """获取所有路径"""
    paths = Config.get_paths()
    # 添加兼容性别名
    paths.update({
        'output_dir': paths['output'],
        'pddl_dir': paths['output_pddl'],
        'plan_dir': paths['output_plan']
    })
    return paths


def get_env_config() -> Dict[str, str]:
    """获取环境配置"""
    return Config.get_env_config()


def ensure_directories(dirs: Optional[list] = None) -> None:
    """确保目录存在"""
    if dirs is None:
        Config.ensure_directories()
    else:
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


def validate_config() -> Dict[str, bool]:
    """验证配置"""
    return Config.validate_config()