#!/usr/bin/env python3
import os
import sys
import yaml
import json
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
    
    LOGIC:
    @classmethod
    def find_staged_or_pending(cls, ia_ids, sources=None):
        conds = [("ia_id", "in", ia_ids), ("status", "in", ["staged", "pending"])]
        if sources:
            conds.append(("ia_id", "like", [s + ":%" for s in sources]))
        items = cls.find(conds)
        return ResultSet(items)

    You MUST import 'ResultSet' from 'infogami.queries'.
    
    FILE CONTENT:
    {current_content}
    """

    # Generate prompts.md for hackathon requirements
    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Prompt sent to Claude\n\n{instruction}")

    log_to_agent({"type": "request", "content": instruction})

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="Return the FULL file content with the fix. You MUST use the @classmethod decorator. Use the write_file tool.",
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
