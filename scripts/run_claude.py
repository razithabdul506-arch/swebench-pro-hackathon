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
    """Core tool for applying the code fix."""
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

    with open(args.task_file, 'r') as f:
        task = yaml.safe_load(f)

    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    instruction = f"Task: {task['description']}\nRequirements: {task['requirements']}\nInterface: {task['interface']}"

    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Evaluation Context\n\n{instruction}")

    log_to_agent({"type": "request", "content": instruction})

    # 🔥 MODEL UPDATE: Using the specific version requested in the PDF
    # If this fails, replace with 'claude-3-5-sonnet-20241022'
    response = client.messages.create(
        model="claude-3-7-sonnet-latest", 
        max_tokens=4096,
        tools=[{
            "name": "write_file",
            "description": "Write content to a file to apply the fix",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["file_path", "content"]
            }
        }],
        messages=[{"role": "user", "content": instruction}],
    )

    log_to_agent({"type": "response", "content": str(response.content)})

    if response.stop_reason == "tool_use":
        for content_block in response.content:
            if content_block.type == "tool_use" and content_block.name == "write_file":
                result = write_file(content_block.input["file_path"], content_block.input["content"])
                log_to_agent({
                    "type": "tool_use", 
                    "tool": "write_file", 
                    "args": content_block.input, 
                    "result": result
                })

if __name__ == "__main__":
    main()
