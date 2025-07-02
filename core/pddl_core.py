import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from jinja2 import Template, Environment, FileSystemLoader

# 导入项目模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_paths, get_env_config, ensure_directories, Config
from constants import PlanningConstants, FileConstants, ValidationConstants
from error_handler import (
    PDDLError, PlanningError, TemplateError, ConfigurationError,
    retry_on_error, safe_execute, default_error_handler
)

try:
    from .explain_plan import explain_plan, explain_plan_content
except ImportError:
    from explain_plan import explain_plan, explain_plan_content

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_problem_file(task: Dict[str, Any], output_path: Path) -> Path:
    """
    从任务参数生成 PDDL 问题文件
    
    Args:
        task: 包含任务参数的字典 (robot, start, goal, domain)
        output_path: 输出问题文件的路径
        
    Returns:
        生成的问题文件路径
        
    Raises:
        TemplateError: 当模板处理失败时
        ConfigurationError: 当参数缺失时
    """
    # 验证必需参数
    required_params = ValidationConstants.REQUIRED_TASK_PARAMS
    missing_params = [param for param in required_params if param not in task]
    if missing_params:
        raise ConfigurationError(f"缺少必需参数: {', '.join(missing_params)}")
    
    try:
        # 获取模板路径
        paths = get_paths()
        template_dir = paths['templates']
        
        # 设置 Jinja2 环境
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template(FileConstants.PROBLEM_TEMPLATE)
        
        # 渲染模板
        problem_content = template.render(
            domain=task['domain'],
            robot=task['robot'],
            start=task['start'],
            goal=task['goal']
        )
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入问题文件
        file_config = Config.get_file_config()
        with open(output_path, 'w', encoding=file_config['encoding']) as f:
            f.write(problem_content)
        
        logger.info(f"✅ 问题文件已生成：{output_path}")
        return output_path
        
    except Exception as e:
        raise TemplateError(f"生成问题文件失败: {str(e)}", original_error=e)

def get_next_index(output_dir: Path, prefix: str = "plan", ext: str = ".txt") -> int:
    """获取下一个文件索引号
    
    Args:
        output_dir: 输出目录路径
        prefix: 文件前缀
        ext: 文件扩展名
        
    Returns:
        下一个可用的索引号
        
    Raises:
        ConfigurationError: 当输出目录不存在时
    """
    if not output_dir.exists():
        raise ConfigurationError(f"输出目录不存在: {output_dir}")
    
    try:
        files = [f for f in os.listdir(output_dir) if f.startswith(prefix) and f.endswith(ext)]
        indices = [int(f.replace(prefix, "").replace(ext, "")) for f in files if f[len(prefix):-len(ext)].isdigit()]
        return max(indices + [0]) + 1
    except Exception as e:
        logger.warning(f"获取文件索引时出错: {e}，使用默认索引 1")
        return 1

def generate_plan(domain_path: Path, problem_path: Path, output_dir: Path, 
                 prefix: str = None, ext: str = None) -> Tuple[Optional[Path], Optional[Path]]:
    """
    生成 PDDL 计划（带动态重试配置）
    """
    # 获取配置
    planning_config = Config.get_planning_config()
    file_config = Config.get_file_config()
    
    # 使用配置中的默认值
    if prefix is None:
        prefix = file_config['plan_prefix']
    if ext is None:
        ext = file_config['plan_extension']
    
    # 应用重试装饰器
    @retry_on_error(
        max_retries=planning_config['max_retries'], 
        delay=planning_config['retry_delay'],
        backoff_factor=planning_config['backoff_factor']
    )
    def _generate_plan_impl() -> Tuple[Optional[Path], Optional[Path]]:
        """生成 PDDL 计划的内部实现
        
        Args:
            domain_path: 领域文件路径
            problem_path: 问题文件路径
            output_dir: 输出目录
            prefix: 文件前缀
            ext: 文件扩展名
            
        Returns:
            计划文件路径和日志文件路径的元组
            
        Raises:
            PlanningError: 当规划失败时
            ConfigurationError: 当配置错误时
        """
        try:
            next_index = get_next_index(output_dir, prefix, ext)
            plan_path = output_dir / f"{prefix}{next_index}{ext}"
            log_path = output_dir / f"{file_config['log_prefix']}{next_index}{file_config['log_extension']}"
        
            # 获取环境配置
            env_config = get_env_config()
            downward_path = env_config['FAST_DOWNWARD_PATH']
            
            # 检查是否为WSL命令格式
            if downward_path.startswith('wsl '):
                # WSL命令格式：将路径转换为WSL格式
                wsl_domain_path = str(domain_path).replace('\\', '/').replace('d:', '/mnt/d').replace('D:', '/mnt/d')
                wsl_problem_path = str(problem_path).replace('\\', '/').replace('d:', '/mnt/d').replace('D:', '/mnt/d')
                
                # 分割WSL命令
                wsl_parts = downward_path.split()
                cmd = wsl_parts + [
                     wsl_domain_path,
                     wsl_problem_path,
                     "--search", f"'{planning_config['search_algorithm']}'"
                 ]
            else:
                # 普通命令格式
                cmd = [
                    sys.executable, downward_path,
                    str(domain_path),
                    str(problem_path),
                    "--search", planning_config['search_algorithm']
                ]
        
            logger.info(f"执行规划命令: {' '.join(cmd)}")
            
            with open(log_path, "w", encoding=file_config['encoding']) as log:
                result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=planning_config['timeout'])
            
            if os.path.exists(file_config['sas_plan_file']):
                os.rename(file_config['sas_plan_file'], plan_path)
                logger.info(f"✅ 计划已生成：{plan_path}")
                return plan_path, log_path
            else:
                # 读取日志文件以获取错误信息
                error_info = ""
                if log_path.exists():
                    with open(log_path, 'r', encoding=file_config['encoding']) as f:
                        error_info = f.read()[-planning_config['error_log_length']:]
            
                raise PlanningError(
                    f"Fast Downward 未生成计划文件",
                    details={
                        'command': ' '.join(cmd),
                        'log_file': str(log_path),
                        'error_output': error_info
                    }
                )
                
        except subprocess.TimeoutExpired:
            raise PlanningError(f"规划器执行超时（{planning_config['timeout']}秒）")
        except Exception as e:
            if isinstance(e, PDDLError):
                raise
            raise PlanningError(f"规划过程中发生错误: {str(e)}", original_error=e)
    
    # 调用内部实现
    return _generate_plan_impl()

def run_mcp_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    运行 MCP 任务
    
    Args:
        task: 包含任务参数的字典
        
    Returns:
        包含执行结果的字典
        
    Raises:
        ConfigurationError: 当参数配置错误时
        PlanningError: 当规划失败时
        TemplateError: 当模板处理失败时
    """
    # 获取任务参数
    domain_path = task.get('domain_path')
    problem_path = task.get('problem_path')
    output_dir = task.get('output_dir', str(get_paths()['output']))
    
    # 验证必需参数
    required_file_params = ValidationConstants.REQUIRED_FILE_PARAMS
    missing_params = [param for param in required_file_params if not task.get(param)]
    if missing_params:
        raise ConfigurationError(f"缺少必需参数：{', '.join(missing_params)}")
    
    # 转换为 Path 对象
    domain_path = Path(domain_path)
    problem_path = Path(problem_path)
    output_dir = Path(output_dir)
    
    # 验证领域文件存在性
    if not domain_path.exists():
        raise ConfigurationError(f"领域文件不存在: {domain_path}")
    
    # 如果问题文件不存在，尝试从任务参数生成
    if not problem_path.exists():
        logger.info(f"问题文件不存在，尝试从任务参数生成: {problem_path}")
        required_task_params = ValidationConstants.REQUIRED_TASK_PARAMS
        if all(param in task for param in required_task_params):
            generate_problem_file(task, problem_path)
        else:
            missing_task_params = [param for param in required_task_params if param not in task]
            raise ConfigurationError(f"问题文件不存在且缺少生成所需参数: {', '.join(missing_task_params)}")
    
    # 确保输出目录存在
    ensure_directories([output_dir])
    
    logger.info(f"开始执行 PDDL 任务: {domain_path} -> {problem_path}")
    
    # 生成计划
    plan_path, log_path = generate_plan(domain_path, problem_path, output_dir)
    
    if plan_path and plan_path.exists():
        # 读取计划内容
        file_config = Config.get_file_config()
        with open(plan_path, 'r', encoding=file_config['encoding']) as f:
            plan_content = f.read()
        
        # 解释计划
        explanation = explain_plan_content(plan_content)
        
        logger.info(f"任务执行成功，计划文件: {plan_path}")
        
        return {
            "success": True,
            "plan_path": str(plan_path),
            "log_path": str(log_path) if log_path else None,
            "plan_content": plan_content,
            "explanation": explanation,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise PlanningError(
            "计划生成失败",
            details={
                "log_path": str(log_path) if log_path else None,
                "domain_path": str(domain_path),
                "problem_path": str(problem_path)
            }
        )

# 使用 safe_execute 包装函数
_original_run_mcp_task = run_mcp_task

def run_mcp_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """安全执行 MCP 任务的包装函数"""
    try:
        return _original_run_mcp_task(task)
    except Exception as e:
        logger.error(f"MCP 任务执行失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "plan_content": "",
            "explanation": "任务执行失败",
            "summary": {"reached_goal": False, "steps": 0}
        }

def extract_task_from_text(text: str) -> Dict[str, str]:
    """从文本中提取任务信息
    
    Args:
        text: 包含任务信息的文本
        
    Returns:
        包含任务参数的字典
        
    Raises:
        ConfigurationError: 当文本格式错误时
    """
    if not text or not text.strip():
        raise ConfigurationError("输入文本为空")
    
    lines = text.strip().split('\n')
    task = {}
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if ':' not in line:
            continue
            
        key, value = line.split(':', 1)
        key = key.strip().lower()
        value = value.strip()
        
        if key == 'domain':
            task['domain_path'] = value
        elif key == 'problem':
            task['problem_path'] = value
        elif key == 'output':
            task['output_dir'] = value
    
    # 验证必需字段
    if 'domain_path' not in task or 'problem_path' not in task:
        raise ConfigurationError(
            "文本中缺少必需的 domain 或 problem 字段\n"
            "格式示例:\n"
            "domain: path/to/domain.pddl\n"
            "problem: path/to/problem.pddl\n"
            "output: path/to/output (可选)"
        )
    
    # 设置默认输出目录
    if 'output_dir' not in task:
        paths = get_paths()
        task['output_dir'] = str(paths['output_dir'])
    
    logger.info(f"从文本提取任务: {task}")
    return task

# === 主程序执行部分 ===
if __name__ == "__main__":
    # 使用相对路径，基于当前文件位置
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TASK_PATH = os.path.join(BASE, "tasks", "task1.json")
    
    # 加载任务
    with open(TASK_PATH, "r") as f:
        task = json.load(f)
    
    # 执行任务
    result = run_mcp_task(task)
    
    # 输出 JSON 格式结果（用于 MCP 集成）
    print(json.dumps(result, ensure_ascii=False, indent=2))
