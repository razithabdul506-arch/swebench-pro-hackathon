#!/usr/bin/env python3
import os
import sys
import yaml
from anthropic import Anthropic

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
    target_file = task['files_to_modify'][0]
    
    with open(target_file, 'r') as f:
        current_content = f.read()

    instruction = f"""
    TASK: In the 'ImportItem' class, add 'find_staged_or_pending' as a @classmethod.
    It must return 'ResultSet(items)' using 'from infogami.queries import ResultSet'.
    
    FILE CONTENT:
    {current_content}
    """

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="Return the FULL file content with the fix. Use the write_file tool.",
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

if __name__ == "__main__":
    main()
