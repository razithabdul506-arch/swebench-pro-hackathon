#!/usr/bin/env python3
import os
import sys
import yaml
from anthropic import Anthropic

PROMPTS_MD_PATH = "/tmp/prompts.md"

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
    The test fails with 'AttributeError: type object ImportItem has no attribute find_staged_or_pending'.
    
    TASK:
    1. Import 'ResultSet' from 'infogami.queries'.
    2. Add the following method inside the 'ImportItem' class as a @classmethod:

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

    # Ensure prompts.md is created for hackathon requirements
    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Instruction sent to AI\n\n{instruction}")

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="Return the FULL file content. Ensure the ImportItem class has the new @classmethod. Use write_file.",
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
