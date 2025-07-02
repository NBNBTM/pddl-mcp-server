from constants import ValidationConstants, DomainConstants
from config import Config

def explain_plan_content(plan_content):
    """从计划内容生成解释
    
    Args:
        plan_content: 计划文件的内容字符串
        
    Returns:
        解释文本字符串
    """
    lines = []
    for line in plan_content.split('\n'):
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if "(" in line and ")" in line:
            start = line.find("(")
            end = line.find(")")
            action_text = line[start + 1:end]
            parts = action_text.strip().split()
            min_parts = ValidationConstants.MIN_ACTION_PARTS
            if len(parts) >= min_parts and parts[0] == DomainConstants.MOVE_ACTION:
                robot, frm, to = parts[1], parts[2], parts[3]
                lines.append(f"Robot {robot} moves from {frm} to {to}.")
    
    return "\n".join(lines)

def explain_plan(plan_path, explanation_path):
    lines = []
    file_config = Config.get_file_config()
    
    with open(plan_path, "r", encoding=file_config['encoding']) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if "(" in line and ")" in line:
                start = line.find("(")
                end = line.find(")")
                action_text = line[start + 1:end]
                parts = action_text.strip().split()
                min_parts = ValidationConstants.MIN_ACTION_PARTS
                if len(parts) >= min_parts and parts[0] == DomainConstants.MOVE_ACTION:
                    robot, frm, to = parts[1], parts[2], parts[3]
                    lines.append(f"Robot {robot} moves from {frm} to {to}.")

    with open(explanation_path, "w", encoding=file_config['encoding']) as out:
        out.write("\n".join(lines))

    print(f"✅ 解释已生成：{explanation_path}")

if __name__ == "__main__":
    import sys
    expected_args = ValidationConstants.EXPECTED_CLI_ARGS
    if len(sys.argv) != expected_args:
        print("Usage: python3 explain_plan.py <plan_path> <explanation_path>")
        sys.exit(1)
    
    plan_path = sys.argv[1]
    explanation_path = sys.argv[2]
    explain_plan(plan_path, explanation_path)

