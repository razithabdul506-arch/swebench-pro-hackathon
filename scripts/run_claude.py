#!/usr/bin/env python3
import os
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

    instruction = f"""
FIX: In the 'ImportItem' class, add 'find_staged_or_pending' as a @classmethod.

Return ONLY the FULL updated file content.

FULL FILE CONTENT:
{current_content}
"""

    # Save prompts.md artifact
    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Prompt sent to AI Agent\n\n{instruction}")

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="Return ONLY the full updated python file. No explanations.",
        messages=[{"role": "user", "content": instruction}],
    )

    updated_content = None

    # --- NEW SAFE PARSING LOGIC ---
    for block in response.content:
        # Case 1: Tool usage
        if getattr(block, "type", "") == "tool_use":
            updated_content = block.input["content"]

        # Case 2: Claude returned plain text
        elif getattr(block, "type", "") == "text":
            updated_content = block.text

    if updated_content:
        print("Writing updated file from Claude response...")
        with open(target_file, "w") as f:
            f.write(updated_content)
    else:
        print("WARNING: Claude returned no editable content!")

if __name__ == "__main__":
    main()
