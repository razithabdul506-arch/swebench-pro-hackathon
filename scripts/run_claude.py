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
        entry["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        f.write(json.dumps(entry) + "\n")

def write_file(file_path, content):
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

    task = yaml.safe_load(open(args.task_file, 'r'))
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    prompt = f"Task: {task['description']}\nRequirements: {task['requirements']}\nInterface: {task['interface']}"

    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Prompt context\n\n{prompt}")

    log_to_agent({"type": "request", "content": prompt})

    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
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

    if response.stop_reason == "tool_use":
        tool_use = response.content[-1]
        if tool_use.name == "write_file":
            res = write_file(tool_use.input["file_path"], tool_use.input["content"])
            log_to_agent({"type": "tool_use", "tool": "write_file", "result": res})

if __name__ == "__main__":
    main()
