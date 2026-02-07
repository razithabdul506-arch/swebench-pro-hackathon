#!/usr/bin/env python3
import os
import sys
import json
import yaml
from datetime import datetime
from anthropic import Anthropic

# Mandatory log path for metrics extraction
AGENT_LOG_PATH = "/tmp/agent.log"
PROMPTS_MD_PATH = "/tmp/prompts.md"

def log_to_agent(entry):
    """Logs interactions to agent.log in JSONL format"""
    with open(AGENT_LOG_PATH, "a") as f:
        entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
        f.write(json.dumps(entry) + "\n")

def write_file(file_path, content):
    """Actual tool to let Claude modify the code"""
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    args = parser.parse_args()

    task = yaml.safe_load(open(args.task_file))
    api_key = os.environ.get("CLAUDE_API_KEY")
    
    if not api_key:
        print("Missing CLAUDE_API_KEY")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    prompt = f"""You are an expert software engineer.
Task: {task['description']}
Requirements: {task['requirements']}
Interface: {task['interface']}
Files to modify: {', '.join(task['files_to_modify'])}
"""

    # 1. Save mandatory prompts.md artifact
    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Prompt sent to Claude\n\n{prompt}")

    # 2. Log the initial request
    log_to_agent({"type": "request", "content": prompt})

    print("Sending task to Claude...")

    # 3. Define the tools Claude is allowed to use
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8192,
        tools=[{
            "name": "write_file",
            "description": "Write content to a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["file_path", "content"]
            }
        }],
        messages=[{"role": "user", "content": prompt}],
    )

    # 4. Process the response and execute tools
    log_to_agent({"type": "response", "content": str(response.content)})

    if response.stop_reason == "tool_use":
        tool_use = response.content[-1]
        if tool_use.name == "write_file":
            result = write_file(tool_use.input["file_path"], tool_use.input["content"])
            log_to_agent({"type": "tool_use", "tool": "write_file", "result": result})
            print(f"Claude modified {tool_use.input['file_path']}")

    print(f"Execution complete. Logs saved to {AGENT_LOG_PATH}")

if __name__ == "__main__":
    main()
