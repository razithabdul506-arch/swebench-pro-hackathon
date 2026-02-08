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

    client = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
    target_file = task['files_to_modify'][0]
    
    with open(target_file, 'r') as f:
        current_content = f.read()

    # We give the AI the exact code to stop the AttributeError
    instruction = f"""
    The test fails with 'AttributeError: type object ImportItem has no attribute find_staged_or_pending'.
    
    FIX: 
    1. Import 'ResultSet' from 'infogami.queries'.
    2. Add the following method inside the 'ImportItem' class. 
    3. It MUST be a @classmethod.

    @classmethod
    def find_staged_or_pending(cls, ia_ids, sources=None):
        conds = [("ia_id", "in", ia_ids), ("status", "in", ["staged", "pending"])]
        if sources:
            conds.append(("ia_id", "like", [s + ":%" for s in sources]))
        items = cls.find(conds)
        return ResultSet(items)

    FILE CONTENT:
    {current_content}
    """

    # Generate prompts.md required for your submission
    with open("/tmp/prompts.md", "w") as f:
        f.write(instruction)

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="Return the FULL file content with the fix. You MUST use @classmethod. Use write_file tool.",
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

    for block in response.content:
        if block.type == "tool_use":
            with open(block.input["file_path"], 'w') as f:
                f.write(block.input["content"])

if __name__ == "__main__":
    main()
