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

    with open(args.task_file, 'r') as f:
        task = yaml.safe_load(f)

    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key: sys.exit(1)

    client = Anthropic(api_key=api_key)
    
    target_file = task['files_to_modify'][0]
    current_content = ""
    if os.path.exists(target_file):
        with open(target_file, 'r') as f:
            current_content = f.read()

    instruction = f"Task: {task['description']}\n\nFile: {target_file}\nCurrent Content:\n{current_content}"

    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Evaluation Context\n\n{instruction}")

    log_to_agent({"type": "request", "content": instruction})

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="""You are a senior staff engineer. 
        IMPORTANT: When modifying files, you must provide the FULL file content. 
        Ensure 'ResultSet' is imported from 'infogami.queries'.
        The code must be syntactically perfect for pytest collection.""",
        tools=[{
            "name": "write_file",
            "description": "Overwrite the file with full corrected content.",
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
        for block in response.content:
            if block.type == "tool_use" and block.name == "write_file":
                res = write_file(block.input["file_path"], block.input["content"])
                log_to_agent({"type": "tool_use", "tool": "write_file", "result": res})

if __name__ == "__main__":
    main()
