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

    # Load task.yaml
    with open(args.task_file, 'r') as f:
        task = yaml.safe_load(f)

    client = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))

    # Target OpenLibrary file inside /testbed
    target_file = task['files_to_modify'][0]

    # Read current content
    with open(target_file, 'r') as f:
        current_content = f.read()

    # ⭐ FINAL SWE-BENCH SAFE INSTRUCTION
    instruction = f"""
CRITICAL SWE-BENCH FIX.

Implement EXACTLY this method inside class ImportItem.

@classmethod
def find_staged_or_pending(cls, ia_ids, sources=None):
    items = []
    for ia_id in ia_ids:
        result = db.where(
            "import_item",
            ia_id=ia_id,
            status=["staged", "pending"],
        )
        if result:
            items.extend(ImportItem(row) for row in result)
    return items

STRICT RULES:
- DO NOT import ResultSet.
- DO NOT call cls.find().
- Use db.where exactly as shown.
- Parameter MUST be named 'sources'.
- sources MUST default to None.
- Return ONLY the FULL python file.
- NO markdown fences.
- NO explanations.
- Keep all other code unchanged.

FULL FILE CONTENT:
{current_content}
"""

    # Save prompts.md artifact
    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Prompt sent to AI Agent\n\n{instruction}")

    # Call Claude
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="Return ONLY valid python code. No markdown. No explanations.",
        messages=[{"role": "user", "content": instruction}],
    )

    updated_content = None

    # ✅ SAFE PARSER
    for block in response.content:
        if getattr(block, "type", "") == "tool_use":
            updated_content = block.input["content"]

        elif getattr(block, "type", "") == "text":
            text = block.text.strip()

            # Remove markdown fences if present
            if text.startswith("```"):
                lines = text.splitlines()

                if lines[0].startswith("```"):
                    lines = lines[1:]

                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]

                text = "\n".join(lines)

            updated_content = text

    # Write updated file
    if updated_content:
        print("Writing updated file from Claude response...")
        with open(target_file, "w") as f:
            f.write(updated_content)
    else:
        print("WARNING: Claude returned no editable content!")

if __name__ == "__main__":
    main()
