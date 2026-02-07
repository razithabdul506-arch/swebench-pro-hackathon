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
    
    with open(target_file, 'r') as f:
        current_content = f.read()

    instruction = f"""
    TASK: In the 'ImportItem' class, add 'find_staged_or_pending' as a @classmethod.
    It must return 'ResultSet(items)' using 'from infogami.queries import ResultSet'.
    
    FILE CONTENT:
    {current_content}
    """

    # Create prompts.md for the hackathon requirements
    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Prompt sent to Claude\n\n{instruction}")

    log_to_agent({"type": "request", "content": instruction})

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="""You are a senior staff engineer. 
        You must provide the FULL file content with the fix. 
        The 'find_staged_or_pending' method MUST be a @classmethod inside the ImportItem class.
        Use the write_file tool to save your changes.""",
        tools=[{
            "name": "write_file",
            "description": "Overwrite the file.",
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

    if response.stop_reason == "tool_use":
        for block in response.content:
            if block.type == "tool_use":
                with open(block.input["file_path"], 'w') as f:
                    f.write(block.input["content"])
                log_to_agent({"type": "tool_use", "result": "Success"})

if __name__ == "__main__":
    main()
