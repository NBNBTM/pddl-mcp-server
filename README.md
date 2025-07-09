# PDDL MCP Server

A PDDL planning server based on the FastMCP framework, providing natural language to PDDL planning conversion, execution, and batch processing capabilities.

## ✨ Features

- 🗣️ **Natural Language Processing**: Generate PDDL planning tasks from natural language descriptions
- 🤖 **Automatic Problem Generation**: Create PDDL problem files based on task parameters
- 📦 **Batch Task Processing**: Run multiple tasks in batch and generate detailed execution reports
- 🔒 **Type Safety**: Data validation and type checking with Pydantic
- ⚙️ **Configuration Validation**: Built-in configuration and system info checking

## 📁 Project Structure

```
pddl-mcp/
├── core/                   # Core modules
├── templates/              # PDDL template files
├── tasks/                  # Task configuration files
├── output/                 # Output directory
├── config.py               # Configuration management
├── constants.py            # Constants
├── error_handler.py        # Error handling
├── server.py               # MCP server
├── test_server.py          # Test suite
├── .env                    # Environment variables
└── requirements.txt        # Dependencies
```

## ⚙️ Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Fast Downward

```bash
git clone https://github.com/aibasel/downward.git
cd downward
./build.py
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and set:

```
FAST_DOWNWARD_PATH=/path/to/fast-downward.py
PDDL_DOMAIN_PATH=./templates/domain.pddl
```

## 🔧 MCP Client Configuration

### Claude Desktop

1. **Find the config file:**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`
2. **Add server config:**
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
3. **Restart Claude Desktop**

### Trae AI IDE

1. **Open MCP Settings:**
   - Click settings → MCP Servers
   - Or use shortcut `Ctrl+Shift+M`
2. **Add new server:**
```json
{
  "name": "PDDL Planner",
  "command": "python",
  "args": ["d:/PDDL/pddl-mcp/server.py"],
  "cwd": "d:/PDDL/pddl-mcp",
  "description": "PDDL planning and NLP server"
}
```
3. **Test Connection**

## 🚀 Running & Usage

### Start the Server

```bash
python server.py
```

You should see:
```
✅ PDDL MCP Server initialized
🚀 Starting FastMCP server...
```

### Run Tests

```bash
python test_server.py
```

### Batch Task Processing

```bash
python core/batch_runner.py
```

## 💬 Prompt Examples

### Basic Planning Task

```
Please plan a robot task:
- Robot: robot1
- Start: room1
- Goal: room3
- Task type: delivery

Generate a complete PDDL plan.
```

### Natural Language Planning

```
Robot r2 needs to move from the warehouse to the office. Please generate a complete movement plan.
```

### Multi-Robot Coordination

```
I have a multi-robot coordination task:
1. Robot r1 in room1, needs to go to room5
2. Robot r2 in room3, needs to go to room2
Please generate an individual plan for each robot and analyze possible path conflicts.
```

### Batch Task Processing

```
Please batch process the following robot tasks:
1. r1: room1 → room3 (delivery)
2. r2: room2 → room4 (patrol)
3. r3: room5 → room1 (maintenance)

Generate a batch execution report including execution time and success rate for each task.
```

### System Configuration & Diagnostics

```
Check the configuration status of the PDDL planning system, including:
- Fast Downward path
- Environment variables
- Dependency versions
- System performance
```

```
My PDDL planning task failed with error: [error message]
Please diagnose the problem and provide a solution.
```

## 🧪 Testing Guide

### Prerequisites
- Python 3.8+
- Dependencies installed (`pip install -r requirements.txt`)
- `.env` configured
- Trae IDE imported project

### Server Status
- MCP server should show as connected in Trae IDE

### Testing Methods

#### 1. Trae IDE Direct Test
- System config check
- Simple planning task
- Natural language planning
- Multi-robot coordination
- Batch task processing

#### 2. Command Line
- Start server: `python server.py`
- Run test suite: `python test_server.py`
- Batch tasks: `python core/batch_runner.py`

### Expected Results
- System config check returns JSON with config path, Fast Downward path, env status, output dir
- Planning tasks generate:
  - PDDL problem files (`output/pddl/`)
  - Plan files (`output/plan/`)
  - Explanation files (`output/explanation/`)
- Batch tasks generate:
  - Batch report (`output/report.json`)
  - Analysis (`output/report.md`)
  - Individual task files

### Common Test Scenarios
- Basic move task: single robot, simple path, expect 1-3 steps
- Complex path: robot passes multiple rooms, expect optimal path
- Multi-robot coordination: possible path conflicts, expect conflict analysis and solution
- Error handling: invalid task params, expect clear error message

### Troubleshooting
- **Server fails to start:**
  1. Check dependencies: `pip install -r requirements.txt`
  2. Check Python version: `python --version`
  3. Check `.env` config
- **Planning fails:**
  1. Validate Fast Downward path
  2. Check `templates/domain.pddl`
  3. Check output directory permissions
- **MCP connection fails:**
  1. Restart Trae IDE
  2. Check `.mcp.json` config
  3. Ensure server port is free
- **Files not generated:**
  1. Check `output/` directory permissions
  2. Ensure enough disk space
  3. Validate file paths

### Performance Testing
- **Response time:** Simple task < 2s (run multiple times)
- **Concurrency:** Multiple tasks at once, expect no conflict
- **Large-scale tasks:** 10+ robots, expect successful coordination

### Test Checklist
- [ ] System config check
- [ ] Simple planning task
- [ ] Natural language processing
- [ ] File generation
- [ ] Multi-robot coordination
- [ ] Batch task processing
- [ ] Path conflict analysis
- [ ] Error handling
- [ ] Response time
- [ ] Concurrency
- [ ] Large-scale tasks
- [ ] Memory usage
- [ ] Trae IDE integration
- [ ] MCP protocol compatibility
- [ ] File system operations
- [ ] Config management

### Test Report Template

```
Test Date: [date]
Environment: [OS, Python version]
Scope: [modules tested]

Results:
✅ Passed
❌ Failed
⚠️  Issues

Performance:
- Avg response time: [time]
- Success rate: [percent]
- Resource usage: [memory, CPU]

Suggestions:
[improvements]
```

### Next Steps
- Expand test cases for more complex scenarios
- Optimize performance based on results
- Add new planning algorithms or features
- Improve documentation and API reference

---

**Note:** For issues during testing, check logs in the `output/` directory or run `python test_server.py` for diagnostics.

## 📄 License

MIT License