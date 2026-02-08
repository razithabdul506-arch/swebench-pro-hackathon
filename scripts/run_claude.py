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

    # ✅ STRONG DETERMINISTIC INSTRUCTION
    instruction = f"""
CRITICAL SWE-BENCH FIX.

You MUST implement EXACTLY this method inside class ImportItem.

@classmethod
def find_staged_or_pending(cls, ia_ids, sources=None):
    from infogami.queries import ResultSet
    conds = [
        ("ia_id", "in", ia_ids),
        ("status", "in", ["staged", "pending"]),
    ]
    if sources:
        conds.append(("ia_id", "like", [s + ":%" for s in sources]))
    items = cls.find(conds)
    return ResultSet(items)

STRICT RULES:
- DO NOT rename parameters.
- DO NOT use db.where.
- The parameter MUST be named "sources".
- sources MUST default to None.
- Return ONLY the FULL updated python file.
- NO markdown fences.
- NO explanations.
- Keep all other code unchanged.

FULL FILE CONTENT:
{current_content}
"""

    # Save prompts.md artifact
    with open(PROMPTS_MD_PATH, "w") as f:
        f.write(f"# Prompt sent to AI Agent\n\n{instruction}")

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system="Return ONLY valid python code. No markdown. No explanations.",
        messages=[{"role": "user", "content": instruction}],
    )

    updated_content = None

    # --- SAFE PARSING LOGIC ---
    for block in response.content:
        if getattr(block, "type", "") == "tool_use":
            updated_content = block.input["content"]

        elif getattr(block, "type", "") == "text":
            text = block.text.strip()

            # Remove markdown fences if Claude adds them
            if text.startswith("```"):
                lines = text.splitlines()

                if lines[0].startswith("```"):
                    lines = lines[1:]

                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]

                text = "\n".join(lines)

            updated_content = text

    if updated_content:
        print("Writing updated file from Claude response...")
        with open(target_file, "w") as f:
            f.write(updated_content)
    else:
        print("WARNING: Claude returned no editable content!")

if __name__ == "__main__":
    main()
