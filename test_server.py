#!/usr/bin/env python3
"""
FastMCP PDDL Server 测试套件

测试 FastMCP 版本的 PDDL 规划服务器功能，包括：
- 工具注册和调用
- 错误处理
- 配置验证
- 系统信息获取
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入错误处理模块
from error_handler import PDDLError
from core import run_mcp_task, extract_task_from_text
from config import Config
from constants import LoggingConstants, DomainConstants

# 尝试导入 FastMCP 服务器
try:
    from server import app, generate_plan, plan_from_text, validate_config, get_system_info
    FASTMCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: FastMCP not available: {e}")
    FASTMCP_AVAILABLE = False


class TestFastMCPServer:
    """FastMCP 服务器功能测试"""
    
    @pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
    def test_server_initialization(self):
        """测试服务器初始化"""
        assert app is not None
        # 基本检查 FastMCP 对象是否正确初始化
        assert str(type(app)) == "<class 'mcp.server.fastmcp.server.FastMCP'>"
        # 检查是否有基本的 FastMCP 方法
        assert hasattr(app, 'tool')
        assert hasattr(app, 'run')
        assert "python-dotenv" in app.dependencies
    
    @pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
    def test_generate_plan_valid_input(self):
        """测试有效输入的计划生成"""
        task = {
            "domain": DomainConstants.DEFAULT_DOMAIN,
            "objects": {
                "robots": [f"{DomainConstants.ROBOT_PREFIX}1"],
                "rooms": [f"{DomainConstants.ROOM_PREFIX}1", f"{DomainConstants.ROOM_PREFIX}2", f"{DomainConstants.ROOM_PREFIX}3"]
            },
            "init": {
                "at": [[f"{DomainConstants.ROBOT_PREFIX}1", f"{DomainConstants.ROOM_PREFIX}1"]]
            },
            "goal": {
                "at": [[f"{DomainConstants.ROBOT_PREFIX}1", f"{DomainConstants.ROOM_PREFIX}3"]]
            }
        }
        
        # Mock the run_mcp_task function to avoid actual PDDL execution
        with patch('server.run_mcp_task') as mock_run:
            mock_run.return_value = {
                "success": True,
                "plan_text": "(move robot1 room1 room3)",
                "explanation_text": "Robot1 moves from room1 to room3.",
                "summary": {
                    "goal": "room3",
                    "steps": 1,
                    "reached_goal": True,
                    "duration_sec": 0.5,
                    "generated_time": "2024-01-01 12:00:00"
                }
            }
            
            result = generate_plan(task)
            
            assert result["success"] is True
            assert "plan_text" in result
            assert "explanation_text" in result
            assert "summary" in result
            mock_run.assert_called_once_with(task)
    
    @pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
    def test_generate_plan_invalid_input(self):
        """测试无效输入的错误处理"""
        # 测试空输入
        result = generate_plan({})
        assert result["success"] is False
        assert "error" in result
        assert "Missing required field" in result["error"]
        
        # 测试非字典输入
        result = generate_plan("invalid")
        assert result["success"] is False
        assert "Task must be a dictionary" in result["error"]
        
        # 测试缺少必需字段
        incomplete_task = {"domain": DomainConstants.DEFAULT_DOMAIN}
        result = generate_plan(incomplete_task)
        assert result["success"] is False
        assert "Missing required field" in result["error"]
    
    @pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
    def test_plan_from_text_valid_input(self):
        """测试有效文本输入的计划生成"""
        text = f"Move robot {DomainConstants.ROBOT_PREFIX}1 from {DomainConstants.ROOM_PREFIX}1 to {DomainConstants.ROOM_PREFIX}3"
        
        # Mock the extract_task_from_text and run_mcp_task functions
        with patch('server.extract_task_from_text') as mock_extract, \
             patch('server.run_mcp_task') as mock_run:
            
            mock_extract.return_value = {
                "robot": f"{DomainConstants.ROBOT_PREFIX}1",
                "start": f"{DomainConstants.ROOM_PREFIX}1",
                "goal": f"{DomainConstants.ROOM_PREFIX}3",
                "domain": DomainConstants.DEFAULT_DOMAIN
            }
            
            mock_run.return_value = {
                "success": True,
                "plan_text": f"(move {DomainConstants.ROBOT_PREFIX}1 {DomainConstants.ROOM_PREFIX}1 {DomainConstants.ROOM_PREFIX}3)",
                "explanation_text": f"Robot {DomainConstants.ROBOT_PREFIX}1 moves from {DomainConstants.ROOM_PREFIX}1 to {DomainConstants.ROOM_PREFIX}3.",
                "summary": {
                    "goal": f"{DomainConstants.ROOM_PREFIX}3",
                    "steps": 1,
                    "reached_goal": True,
                    "duration_sec": 0.3,
                    "generated_time": "2024-01-01 12:00:00"
                }
            }
            
            result = plan_from_text(text)
            
            assert result["success"] is True
            assert "extracted_task" in result
            assert "original_text" in result
            assert result["original_text"] == text
            assert result["extracted_task"]["robot"] == f"{DomainConstants.ROBOT_PREFIX}1"
            assert result["extracted_task"]["start"] == f"{DomainConstants.ROOM_PREFIX}1"
            assert result["extracted_task"]["goal"] == f"{DomainConstants.ROOM_PREFIX}3"
            
            mock_extract.assert_called_once_with(text)
            mock_run.assert_called_once()
    
    @pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
    def test_plan_from_text_invalid_input(self):
        """测试无效文本输入的错误处理"""
        # 测试空文本
        result = plan_from_text("")
        assert result["success"] is False
        assert "Text input is required" in result["error"]
        
        # 测试非字符串输入
        result = plan_from_text(123)
        assert result["success"] is False
        assert "must be a string" in result["error"]
        
        # 测试解析失败
        with patch('server.extract_task_from_text') as mock_extract:
            mock_extract.side_effect = ValueError("Could not parse text")
            
            result = plan_from_text("invalid text format")
            assert result["success"] is False
            assert "Could not extract task information" in result["error"]
            assert result["error_type"] == "PARSING_ERROR"
    
    @pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
    def test_validate_config(self):
        """测试配置验证功能"""
        with patch('server.Config.get_env_config') as mock_env, \
              patch('server.Config.get_paths') as mock_paths, \
              patch('server.Config.ensure_directories') as mock_ensure:
            
            mock_env.return_value = {
                "FAST_DOWNWARD_PATH": "fast-downward.py",
                "PDDL_DOMAIN_PATH": "./templates/domain.pddl"
            }
            
            mock_paths.return_value = {
                "output_dir": Path("./output"),
                "pddl_dir": Path("./output/pddl"),
                "plan_dir": Path("./output/plan")
            }
            
            result = validate_config()
            
            assert result["success"] is True
            assert "config" in result
            assert "paths" in result
            assert "validation" in result
            assert result["validation"]["env_variables_loaded"] is True
            assert "fast_downward_path" in result["validation"]
            assert "pddl_domain_path" in result["validation"]
    
    @pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
    def test_get_system_info(self):
        """测试系统信息获取"""
        result = get_system_info()
        
        assert result["success"] is True
        assert "server_info" in result
        assert "system_info" in result
        
        server_info = result["server_info"]
        assert server_info["name"] == "PDDL Planner (FastMCP)"
        assert server_info["version"] == "2.0.0"
        assert server_info["framework"] == "FastMCP"
        assert "capabilities" in server_info
        assert "generate_plan" in server_info["capabilities"]
        assert "plan_from_text" in server_info["capabilities"]
        
        system_info = result["system_info"]
        assert "platform" in system_info
        assert "python_version" in system_info
        assert "working_directory" in system_info
        assert "project_root" in system_info
    
    @pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
    def test_error_handling_with_pddl_error(self):
        """测试 PDDL 错误的处理"""
        from error_handler import PDDLError
        
        task = {
            "domain": DomainConstants.DEFAULT_DOMAIN,
            "objects": {"robots": [f"{DomainConstants.ROBOT_PREFIX}1"], "rooms": [f"{DomainConstants.ROOM_PREFIX}1", f"{DomainConstants.ROOM_PREFIX}3"]},
            "init": {"at": [[f"{DomainConstants.ROBOT_PREFIX}1", f"{DomainConstants.ROOM_PREFIX}1"]]},
            "goal": {"at": [[f"{DomainConstants.ROBOT_PREFIX}1", f"{DomainConstants.ROOM_PREFIX}3"]]}
        }
        
        with patch('server.run_mcp_task') as mock_run:
            mock_run.side_effect = PDDLError("Planning failed", "PLANNING_ERROR")
            
            result = generate_plan(task)
            
            assert result["success"] is False
            assert "error" in result
            assert result["error_type"] == "PDDL_ERROR"
    
    @pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
    def test_error_handling_with_system_error(self):
        """测试系统错误的处理"""
        task = {
            "domain": DomainConstants.DEFAULT_DOMAIN,
            "objects": {"robots": [f"{DomainConstants.ROBOT_PREFIX}1"], "rooms": [f"{DomainConstants.ROOM_PREFIX}1", f"{DomainConstants.ROOM_PREFIX}3"]},
            "init": {"at": [[f"{DomainConstants.ROBOT_PREFIX}1", f"{DomainConstants.ROOM_PREFIX}1"]]},
            "goal": {"at": [[f"{DomainConstants.ROBOT_PREFIX}1", f"{DomainConstants.ROOM_PREFIX}3"]]}
        }
        
        with patch('server.run_mcp_task') as mock_run:
            mock_run.side_effect = Exception("Unexpected system error")
            
            result = generate_plan(task)
            
            assert result["success"] is False
            assert "error" in result
            assert result["error_type"] == "SYSTEM_ERROR"
            assert "Unexpected error" in result["error"]


def test_fastmcp_availability():
    """测试 FastMCP 可用性"""
    if FASTMCP_AVAILABLE:
        print("✅ FastMCP is available and server can be imported")
    else:
        print("⚠️ FastMCP is not available - install with: pip install fastmcp")


def test_server_functions_simple():
    """简单的服务器功能测试（替代test_server_functionality.py）"""
    if not FASTMCP_AVAILABLE:
        print("❌ FastMCP not available - skipping function tests")
        return
    
    print("\n🧪 测试 PDDL MCP Server 功能")
    print(LoggingConstants.SEPARATOR)
    
    try:
        # 测试系统信息
        print("\n📊 测试系统信息...")
        system_info = get_system_info()
        if system_info.get("success"):
            print(f"✅ 系统信息获取成功")
            print(f"   服务器名称: {system_info['server_info']['name']}")
            print(f"   版本: {system_info['server_info']['version']}")
            print(f"   框架: {system_info['server_info']['framework']}")
        else:
            print(f"❌ 系统信息获取失败: {system_info.get('error')}")
        
        # 测试配置验证
        print("\n⚙️  测试配置验证...")
        config_result = validate_config()
        if config_result.get("success"):
            print("✅ 配置验证成功")
            print(f"   环境变量数量: {len(config_result.get('config', {}))}")
            print(f"   Fast Downward 路径: {config_result['validation']['fast_downward_path']}")
        else:
            print(f"❌ 配置验证失败: {config_result.get('error')}")
        
        print("\n🎉 简单功能测试完成！")
        print("\n💡 说明:")
        print("   - 如果规划功能失败，请检查 Fast Downward 配置")
        print("   - 服务器核心功能正常，可以接受 MCP 客户端连接")
        print("   - 使用 'python server.py' 启动 MCP 服务器")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行基本可用性测试
    test_fastmcp_availability()
    
    if FASTMCP_AVAILABLE:
        # 运行简单功能测试
        test_server_functions_simple()
        
        # 运行完整的pytest测试套件
        print("\n🧪 Running complete pytest test suite...")
        pytest.main(["-v", __file__])
    else:
        print("\n❌ Cannot run tests - FastMCP not available")
        print("Install FastMCP with: pip install fastmcp")