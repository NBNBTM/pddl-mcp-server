#!/usr/bin/env python3
"""
PDDL MCP Server (FastMCP Version)

A Model Context Protocol server that provides PDDL planning capabilities using FastMCP.
This server allows clients to generate automated plans for robot movement tasks
and provides natural language explanations of the generated plans.

Optimized with FastMCP for:
- Simplified code structure
- Automatic tool registration
- Better type safety with Pydantic
- Enhanced developer experience
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
from pydantic import Field

# FastMCP import
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: FastMCP not installed. Please install with: pip install fastmcp")
    sys.exit(1)

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from config import Config
from constants import ServerConstants, LoggingConstants
from error_handler import PDDLError, safe_execute, default_error_handler
from core import run_mcp_task, extract_task_from_text

# Create FastMCP Server
app = FastMCP(
    title="PDDL Planner",
    description="A server for PDDL-based automated planning and robot task generation",
    version="2.0.0",
    dependencies=["fastmcp", "jinja2", "python-dotenv", "pydantic"]
)


@app.tool()
def generate_plan(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a PDDL plan for robot movement tasks.
    
    Accepts structured task data with robot, start location, goal location, and domain information.
    Uses Fast Downward planner to generate optimal execution plans.
    
    Args:
        task: Task specification with robot and location information.
              Must include:
              - domain: Domain name (e.g., 'delivery')
              - objects: Dict with 'robots' and 'rooms' lists
              - init: Initial state with 'at' positions
              - goal: Goal state with 'at' positions
              
              Example:
              {
                "domain": "delivery",
                "objects": {
                  "robots": ["robot1"],
                  "rooms": ["room1", "room2", "room3"]
                },
                "init": {
                  "at": [["robot1", "room1"]]
                },
                "goal": {
                  "at": [["robot1", "room3"]]
                }
              }
    
    Returns:
        On success: {
          "success": True,
          "plan_text": "<PDDL plan>",
          "explanation_text": "<natural language explanation>",
          "summary": {
            "goal": "<goal location>",
            "steps": <number of steps>,
            "reached_goal": True,
            "duration_sec": <execution time>,
            "generated_time": "<timestamp>"
          }
        }
        On error: {"success": False, "error": "<error message>"}
    
    Examples:
        >>> generate_plan({
        ...   "domain": "delivery",
        ...   "objects": {"robots": ["r1"], "rooms": ["room1", "room3"]},
        ...   "init": {"at": [["r1", "room1"]]},
        ...   "goal": {"at": [["r1", "room3"]]}
        ... })
        {'success': True, 'plan_text': '(move r1 room1 room3)', ...}
    """
    try:
        # Validate required fields
        if not isinstance(task, dict):
            return {"success": False, "error": "Task must be a dictionary"}
        
        required_fields = ["objects", "init", "goal"]
        for field in required_fields:
            if field not in task:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        # Set default domain if not provided
        if "domain" not in task:
            task["domain"] = "delivery"
        
        # Run the PDDL planning task
        result = run_mcp_task(task)
        
        # Ensure success field is set
        if "success" not in result:
            result["success"] = result.get("plan_text", "") != ""
        
        return result
        
    except PDDLError as e:
        return {
            "success": False,
            "error": e.get_user_message(),
            "error_type": "PDDL_ERROR"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "SYSTEM_ERROR"
        }


@app.tool()
def plan_from_text(text: str) -> Dict[str, Any]:
    """
    Extract task information from natural language text and generate a PDDL plan.
    
    Useful for converting human-readable instructions into automated plans.
    Automatically parses robot names, locations, and generates appropriate PDDL structures.
    
    Args:
        text: Natural language description of the task.
              Examples:
              - "Move robot r1 from room1 to room3"
              - "Send robot2 from kitchen to bedroom"
              - "Navigate bot1 from start to goal"
    
    Returns:
        On success: {
          "success": True,
          "extracted_task": {
            "robot": "<robot name>",
            "start": "<start location>",
            "goal": "<goal location>",
            "domain": "<domain name>"
          },
          "plan_text": "<PDDL plan>",
          "explanation_text": "<natural language explanation>",
          "summary": {...}
        }
        On error: {"success": False, "error": "<error message>"}
    
    Examples:
        >>> plan_from_text("Move robot r1 from room1 to room3")
        {'success': True, 'extracted_task': {'robot': 'r1', 'start': 'room1', 'goal': 'room3', 'domain': 'delivery'}, ...}
        >>> plan_from_text("invalid text")
        {'success': False, 'error': 'Could not extract task information from text'}
    """
    try:
        if not text or not isinstance(text, str):
            return {"success": False, "error": "Text input is required and must be a string"}
        
        # Extract structured task from text
        extracted_task = extract_task_from_text(text)
        
        # Convert to full task format
        task = {
            "domain": extracted_task["domain"],
            "problem": f"robot-{extracted_task['domain']}",
            "objects": {
                "robots": [extracted_task["robot"]],
                "rooms": [extracted_task["start"], extracted_task["goal"]]
            },
            "init": {
                "at": [[extracted_task["robot"], extracted_task["start"]]]
            },
            "goal": {
                "at": [[extracted_task["robot"], extracted_task["goal"]]]
            }
        }
        
        # Run the PDDL planning task
        result = run_mcp_task(task)
        
        # Add extracted task information to result
        result["extracted_task"] = extracted_task
        result["original_text"] = text
        
        # Ensure success field is set
        if "success" not in result:
            result["success"] = result.get("plan_text", "") != ""
        
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "error": f"Could not extract task information from text: {str(e)}",
            "error_type": "PARSING_ERROR"
        }
    except PDDLError as e:
        return {
            "success": False,
            "error": e.get_user_message(),
            "error_type": "PDDL_ERROR"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "SYSTEM_ERROR"
        }


@app.tool()
def validate_config() -> Dict[str, Any]:
    """
    Validate the current PDDL planner configuration.
    
    Checks environment variables, file paths, and system requirements.
    Useful for debugging configuration issues.
    
    Returns:
        Configuration validation results with status and details.
        
    Examples:
        >>> validate_config()
        {'success': True, 'config': {...}, 'validation': {...}}
    """
    try:
        # Get current configuration
        env_config = Config.get_env_config()
        paths = Config.get_paths()
        
        # Perform validation checks
        validation_results = {
            "env_variables_loaded": len(env_config) > 0,
            "fast_downward_path": env_config.get("FAST_DOWNWARD_PATH", "Not set"),
            "pddl_domain_path": env_config.get("PDDL_DOMAIN_PATH", "Not set"),
            "output_directories": {
                "output_dir": str(paths.get("output_dir", "Not configured")),
                "pddl_dir": str(paths.get("pddl_dir", "Not configured")),
                "plan_dir": str(paths.get("plan_dir", "Not configured"))
            }
        }
        
        # Check if directories exist
        try:
            Config.ensure_directories([paths['output_dir'], paths['pddl_dir'], paths['plan_dir']])
            validation_results["directories_created"] = True
        except Exception as e:
            validation_results["directories_created"] = False
            validation_results["directory_error"] = str(e)
        
        return {
            "success": True,
            "config": env_config,
            "paths": {k: str(v) for k, v in paths.items()},
            "validation": validation_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Configuration validation failed: {str(e)}"
        }


@app.tool()
def get_system_info() -> Dict[str, Any]:
    """
    Get system information and server status.
    
    Provides details about the server version, capabilities, and runtime environment.
    
    Returns:
        System information and server status.
    """
    try:
        import platform
        import os
        
        return {
            "success": True,
            "server_info": {
                "name": ServerConstants.NAME,
                "version": ServerConstants.VERSION,
                "framework": "FastMCP",
                "capabilities": ["generate_plan", "plan_from_text", "validate_config", "get_system_info"]
            },
            "system_info": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "working_directory": os.getcwd(),
                "project_root": str(project_root)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Could not retrieve system information: {str(e)}"
        }


def check_dependencies():
    """检查必要的依赖项"""
    required_packages = [
        ('fastmcp', 'FastMCP framework'),
        ('jinja2', 'Template engine'),
        ('pydantic', 'Data validation'),
        ('python-dotenv', 'Environment variables')
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            # 处理包名中的连字符
            import_name = package.replace('-', '_')
            if package == 'python-dotenv':
                import_name = 'dotenv'
            __import__(import_name)
            print(f"✅ {description} ({package}) - OK")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {description} ({package}) - Missing")
    
    if missing_packages:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    return True


def check_configuration():
    """检查配置文件"""
    try:
        env_config = Config.get_env_config()
        paths = Config.get_paths()
        
        print(f"✅ Configuration loaded ({len(env_config)} variables)")
        print(f"✅ Project paths configured")
        
        # 检查关键路径
        fast_downward_path = env_config.get('FAST_DOWNWARD_PATH')
        if fast_downward_path:
            print(f"✅ Fast Downward path: {fast_downward_path}")
        else:
            print("⚠️  Fast Downward path not configured (planning may fail)")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 PDDL MCP Server (FastMCP) - Starting...")
    print("=" * 50)
    
    # 检查依赖项
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # 检查配置
    print("\n⚙️  Checking configuration...")
    if not check_configuration():
        print("\n💡 Tip: Copy .env.example to .env and configure your settings")
        sys.exit(1)
    
    # 启动服务器
    print("\n🎯 Starting FastMCP server...")
    print("=" * 50)
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)