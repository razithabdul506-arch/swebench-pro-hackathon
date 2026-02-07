#!/usr/bin/env python3
import os
import sys
import json
import yaml
from datetime import datetime, timezone
from anthropic import Anthropic

AGENT_LOG_PATH = "/tmp/agent.log"
PROMPTS_MD_PATH = "/tmp/prompts.md"

def log_to_agent(entry):
    with open(AGENT_LOG_PATH, "a") as f:
        # Professional ISO format for metrics extraction
        entry["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        f.write(json.dumps(entry) + "\n")

def write_file(file_path, content):
    """Tool implementation to modify the codebase"""
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

    if not os.path.exists(args.task_file):
        sys.exit(1)

    with open(args.task_file, 'r') as f:
        task = yaml.safe_load(f)

    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    prompt = f"Task: {task['description']}\nRequirements: {task['requirements']}\nInterface: {task['interface']}"

    # Generate required prompts artifact
    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Prompt Context\n\n{prompt}")

    log_to_agent({"type": "request", "content": prompt})

    # Call Claude with tool definitions
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022", 
        max_tokens=4096,
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

    log_to_agent({"type": "response", "content": str(response.content)})

    # Execute the tool if Claude requested it
    if response.stop_reason == "tool_use":
        tool_use = response.content[-1]
        if tool_use.name == "write_file":
            # This call now works because write_file is defined above
            res = write_file(tool_use.input["file_path"], tool_use.input["content"])
            log_to_agent({
                "type": "tool_use", 
                "tool": "write_file", 
                "args": tool_use.input, 
                "result": res
            })

if __name__ == "__main__":
    main()
