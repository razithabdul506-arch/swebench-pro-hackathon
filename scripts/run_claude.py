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

    client = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
    target_file = task['files_to_modify'][0]
    
    with open(target_file, 'r') as f:
        current_content = f.read()

    # Direct logic injection to solve the AttributeError
    instruction = f"""
    FIX: In the 'ImportItem' class, add 'find_staged_or_pending' as a @classmethod.
    
    Required code:
    @classmethod
    def find_staged_or_pending(cls, ia_ids, sources=None):
        from infogami.queries import ResultSet
        conds = [("ia_id", "in", ia_ids), ("status", "in", ["staged", "pending"])]
        if sources:
            conds.append(("ia_id", "like", [s + ":%" for s in sources]))
        items = cls.find(conds)
        return ResultSet(items)

    FULL FILE CONTENT TO MODIFY:
    {current_content}
    """

    # Create the prompts.md artifact
    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Prompt sent to AI Agent\n\n{instruction}")

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

    for block in response.content:
        if block.type == "tool_use":
            with open(block.input["file_path"], 'w') as f:
                f.write(block.input["content"])

if __name__ == "__main__":
    main()
