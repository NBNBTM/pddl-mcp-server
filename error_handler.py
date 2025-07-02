#!/usr/bin/env python3
"""
错误处理模块

提供统一的错误处理、分类、重试机制和用户友好的错误信息。
"""

import logging
import time
import traceback
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union
from constants import ErrorConstants


class ErrorType(Enum):
    """错误类型枚举"""
    PARSING = "parsing_error"
    PLANNING = "planning_error"
    FILE_IO = "file_io_error"
    NETWORK = "network_error"
    TIMEOUT = "timeout_error"
    VALIDATION = "validation_error"
    CONFIGURATION = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class PDDLError(Exception):
    """PDDL 相关错误的基类"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 details: Optional[Dict[str, Any]] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_type': self.error_type.value,
            'message': str(self),
            'details': self.details,
            'timestamp': self.timestamp,
            'original_error': str(self.original_error) if self.original_error else None
        }
    
    def get_user_friendly_message(self) -> str:
        """获取用户友好的错误信息"""
        error_messages = {
            ErrorType.PARSING: "解析错误：输入格式不正确",
            ErrorType.PLANNING: "规划失败：无法生成有效计划",
            ErrorType.FILE_IO: "文件操作错误：无法读取或写入文件",
            ErrorType.NETWORK: "网络错误：连接失败",
            ErrorType.TIMEOUT: "超时错误：操作耗时过长",
            ErrorType.VALIDATION: "验证错误：输入数据无效",
            ErrorType.CONFIGURATION: "配置错误：系统配置不正确",
            ErrorType.UNKNOWN_ERROR: "未知错误：请联系技术支持"
        }
        
        base_message = error_messages.get(self.error_type, "发生了未知错误")
        return f"{base_message}\n详细信息：{str(self)}"
    
    def get_user_message(self) -> str:
        """获取用户消息（兼容性方法）"""
        return self.get_user_friendly_message()


class ConfigurationError(PDDLError):
    """配置错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorType.CONFIGURATION, **kwargs)


class PlanningError(PDDLError):
    """规划错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorType.PLANNING, **kwargs)


class TemplateError(PDDLError):
    """模板错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorType.PARSING, **kwargs)


class ParsingError(PDDLError):
    """解析错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorType.PARSING, **kwargs)


class ValidationError(PDDLError):
    """验证错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorType.VALIDATION, **kwargs)


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> PDDLError:
        """处理错误并转换为 PDDLError"""
        context = context or {}
        
        # 如果已经是 PDDLError，直接返回
        if isinstance(error, PDDLError):
            self.logger.error(f"PDDL Error: {error.get_user_friendly_message()}", extra=context)
            return error
        
        # 根据错误类型进行分类
        error_type = self._classify_error(error)
        
        # 创建 PDDLError
        pddl_error = PDDLError(
            message=str(error),
            error_type=error_type,
            details=context,
            original_error=error
        )
        
        # 记录错误
        self.logger.error(
            f"Error handled: {error_type.value}", 
            extra={
                'error_message': str(error),
                'error_type': error_type.value,
                'context': context,
                'traceback': traceback.format_exc()
            }
        )
        
        return pddl_error
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """根据异常类型分类错误"""
        error_name = type(error).__name__
        error_message = str(error).lower()
        
        # 文件相关错误
        if isinstance(error, (FileNotFoundError, IOError)) or 'no such file' in error_message:
            return ErrorType.FILE_IO
        
        # 模板相关错误
        if 'template' in error_message or 'jinja' in error_message:
            return ErrorType.PARSING
        
        # 解析相关错误
        if isinstance(error, (ValueError, TypeError, KeyError)) or 'json' in error_message:
            return ErrorType.PARSING
        
        # 环境相关错误
        if isinstance(error, (OSError, EnvironmentError)) or 'command not found' in error_message:
            return ErrorType.CONFIGURATION
        
        # 超时错误
        if 'timeout' in error_message or isinstance(error, TimeoutError):
            return ErrorType.TIMEOUT
        
        # 网络错误
        if 'connection' in error_message or 'network' in error_message:
            return ErrorType.NETWORK
        
        return ErrorType.UNKNOWN_ERROR


def retry_on_error(max_retries: int = ErrorConstants.DEFAULT_MAX_RETRIES, 
                  delay: float = ErrorConstants.DEFAULT_DELAY, 
                  backoff_factor: float = ErrorConstants.DEFAULT_BACKOFF_FACTOR, 
                  retry_on: tuple = (Exception,)):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt < max_retries:
                        sleep_time = delay * (backoff_factor ** attempt)
                        logging.warning(
                            f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {str(e)}. "
                            f"等待 {sleep_time:.2f} 秒后重试..."
                        )
                        time.sleep(sleep_time)
                    else:
                        logging.error(f"函数 {func.__name__} 在 {max_retries + 1} 次尝试后仍然失败: {str(e)}")
                        break
            
            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception
        
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, error_handler: Optional[ErrorHandler] = None, 
                context: Optional[Dict[str, Any]] = None, **kwargs) -> tuple[Any, Optional[PDDLError]]:
    """安全执行函数，返回结果和错误"""
    error_handler = error_handler or ErrorHandler()
    
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        error = error_handler.handle_error(e, context)
        return None, error


# 全局错误处理器实例
default_error_handler = ErrorHandler()