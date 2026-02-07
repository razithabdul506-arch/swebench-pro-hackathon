#!/usr/bin/env python3
import os
import sys
import json
import yaml
from anthropic import Anthropic

def write_file(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)
    return {"success": True}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    args = parser.parse_args()

    with open(args.task_file, 'r') as f:
        task = yaml.safe_load(f)

    client = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
    target_file = task['files_to_modify'][0]
    
    with open(target_file, 'r') as f:
        current_content = f.read()

    # We give Claude a very strict role and the specific fix required
    instruction = f"""TASK: Return 'ResultSet' instead of a list in find_staged_or_pending.
    FILE: {target_file}
    CONTENT:
    {current_content}
    """

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="You are a senior dev. Use 'write_file' to return the FULL file content. Ensure 'from infogami.queries import ResultSet' is present and the method returns 'ResultSet(items)'.",
        tools=[{
            "name": "write_file",
            "description": "Save the fixed file.",
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

    for block in response.content:
        if block.type == "tool_use" and block.name == "write_file":
            write_file(block.input["file_path"], block.input["content"])

if __name__ == "__main__":
    main()
