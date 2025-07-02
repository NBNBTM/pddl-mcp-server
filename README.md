# PDDL MCP Server

基于 FastMCP 框架的 PDDL 规划服务器，提供自然语言到 PDDL 规划的转换和执行功能。

## ✨ 特性

- 🗣️ **自然语言处理**: 支持从自然语言描述生成 PDDL 规划任务
- 🤖 **自动问题生成**: 根据任务参数自动生成 PDDL 问题文件
- 📦 **批量任务处理**: 支持批量运行多个任务，生成详细的执行报告
- 🔒 **类型安全**: 使用 Pydantic 进行数据验证和类型检查
- ⚙️ **配置验证**: 内置配置验证和系统信息获取

## 🎯 功能

- **generate_plan**: 从结构化任务数据生成 PDDL 规划
- **plan_from_text**: 从自然语言描述生成规划
- **validate_config**: 验证系统配置和环境设置
- **get_system_info**: 获取系统状态和版本信息

## 📁 项目结构

```
pddl-mcp/
├── core/                   # 核心模块
├── templates/              # PDDL 模板文件
├── tasks/                  # 任务配置文件
├── output/                 # 输出目录
├── config.py               # 配置管理
├── constants.py            # 常量定义
├── error_handler.py        # 错误处理
├── server.py               # MCP 服务器
├── test_server.py          # 测试套件
├── .env                    # 环境变量
└── requirements.txt        # 依赖包列表
```

## ⚙️ 安装配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 Fast Downward

```bash
# 下载并编译 Fast Downward
git clone https://github.com/aibasel/downward.git
cd downward
./build.py
```

### 3. 环境配置

复制 `.env.example` 到 `.env` 并配置：

```bash
FAST_DOWNWARD_PATH=/path/to/fast-downward.py
PDDL_DOMAIN_PATH=./templates/domain.pddl
```

## 🔧 MCP 客户端配置

### Claude Desktop 配置

1. **找到配置文件**：
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **添加服务器配置**：
```json
{
  "mcpServers": {
    "pddl-planner": {
      "command": "python",
      "args": ["d:/PDDL/pddl-mcp/server.py"],
      "cwd": "d:/PDDL/pddl-mcp",
      "env": {
        "FAST_DOWNWARD_PATH": "/path/to/fast-downward.py"
      }
    }
  }
}
```

3. **重启 Claude Desktop** 使配置生效

### Trae AI IDE 配置

1. **打开 MCP 设置**：
   - 点击设置图标 → MCP Servers
   - 或使用快捷键 `Ctrl+Shift+M`

2. **添加新服务器**：
```json
{
  "name": "PDDL Planner",
  "command": "python",
  "args": ["d:/PDDL/pddl-mcp/server.py"],
  "cwd": "d:/PDDL/pddl-mcp",
  "description": "PDDL规划和自然语言处理服务器"
}
```

3. **测试连接**：点击 "Test Connection" 验证配置

## 🚀 启动和使用

### 启动服务器

```bash
python server.py
```

成功启动后会看到：
```
✅ PDDL MCP Server initialized
🚀 Starting FastMCP server...
```

### 测试

```bash
# 运行测试套件
python test_server.py
```

## 💬 提示词示例

### 基础规划任务

**提示词**：
```
请帮我规划一个机器人任务：
- 机器人：robot1
- 起始位置：room1
- 目标位置：room3
- 任务类型：delivery

请生成完整的PDDL规划方案。
```

### 自然语言规划

**提示词**：
```
机器人r2需要从仓库移动到办公室，请帮我生成一个完整的移动计划。
```

**复杂任务提示词**：
```
我有一个多机器人协调任务：
1. 机器人r1在room1，需要到room5
2. 机器人r2在room3，需要到room2
请为每个机器人生成独立的规划方案，并分析可能的路径冲突。
```

### 批量任务处理

**提示词**：
```
请帮我批量处理以下机器人任务：
1. r1: room1 → room3 (delivery)
2. r2: room2 → room4 (patrol)
3. r3: room5 → room1 (maintenance)

生成批量执行报告，包括每个任务的执行时间和成功率。
```

### 系统配置和诊断

**配置检查提示词**：
```
请检查PDDL规划系统的配置状态，包括：
- Fast Downward路径配置
- 环境变量设置
- 依赖包版本
- 系统性能指标
```

**故障诊断提示词**：
```
我的PDDL规划任务失败了，错误信息是：[具体错误信息]
请帮我诊断问题并提供解决方案。
```

### 可用工具

- **generate_plan(task)**: 从结构化任务数据生成 PDDL 规划
- **plan_from_text(text)**: 从自然语言描述生成规划
- **validate_config()**: 验证系统配置和环境设置
- **get_system_info()**: 获取系统状态和版本信息

## 📄 许可证

MIT License