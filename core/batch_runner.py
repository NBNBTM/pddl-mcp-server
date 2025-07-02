import os
import subprocess
import json
from datetime import datetime
import time
import sys

# 添加当前目录到 Python 路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pddl_core import run_mcp_task
from explain_plan import explain_plan

# 使用相对路径，基于当前文件位置
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK_DIR = os.path.join(BASE, "tasks")
REPORT_JSON = os.path.join(BASE, "output/report.json")
REPORT_MD = os.path.join(BASE, "output/report.md")

summary_data = []
run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 遍历所有 task 文件
for filename in sorted(os.listdir(TASK_DIR)):
    if filename.endswith(".json"):
        task_path = os.path.join(TASK_DIR, filename)
        print(f"🚀 运行任务：{filename}")

        # 执行 MCP 工具，直接调用函数
        with open(task_path, "r") as f:
            task = json.load(f)
        result = run_mcp_task(task)

        # 构建 summary 数据
        summary = {
            "task_file": filename,
            "generated_time": result.get("timestamp", ""),
            "reached_goal": result.get("success", False),
            "plan_file": result.get("plan_path", ""),
            "explanation_file": "",
            "steps": len(result.get("plan_content", "").split("\n")) if result.get("plan_content") else 0,
            "duration_sec": "N/A",
            "cost_line": "Cost: N/A"
        }
        
        # 生成解释文件
        if result.get("success") and result.get("plan_path"):
            explanation_filename = filename.replace(".json", "_explanation.txt")
            explanation_path = os.path.join(BASE, "output/explanation", explanation_filename)
            
            # 确保解释目录存在
            os.makedirs(os.path.dirname(explanation_path), exist_ok=True)
            
            # 写入解释内容
            with open(explanation_path, "w", encoding='utf-8') as f:
                f.write(result.get("explanation", "无解释内容"))
            
            summary["explanation_file"] = explanation_path
            print(f"✅ 解释已生成：{explanation_path}")
        else:
            print(f"⚠️ 跳过解释生成：任务执行失败或无计划文件")
            
        summary_data.append(summary)

# 输出 JSON 汇总
with open(REPORT_JSON, "w") as f:
    json.dump(summary_data, f, indent=2)
print(f"✅ 已生成 JSON 报告：{REPORT_JSON}")

# 输出 Markdown 报告
with open(REPORT_MD, "w") as f:
    f.write(f"# 🧾 MCP 批量任务执行报告\n\n批处理生成时间：{run_time}\n\n")
    for item in summary_data:
        f.write(f"## 🔹 Task: {item['task_file']}\n")
        f.write(f"- ⏰ 生成时间: {item.get('generated_time', '')}\n")
        f.write(f"- ✅ Reached Goal: {'✅ 是' if item.get('reached_goal') else '❌ 否'}\n")
        f.write(f"- 📄 Plan: `{item['plan_file']}`\n")
        f.write(f"- 💬 Explanation: `{item['explanation_file']}`\n")
        f.write(f"- 🔢 Steps: {item.get('steps', '')} | ⏱ Time: {item.get('duration_sec', '')}s\n")
        f.write(f"- 💰 {item.get('cost_line', '')}\n\n")
print(f"✅ 已生成 Markdown 报告：{REPORT_MD}")
