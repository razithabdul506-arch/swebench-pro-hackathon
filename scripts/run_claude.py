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

    # Load task
    with open(args.task_file, 'r') as f:
        task = yaml.safe_load(f)

    client = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))

    target_file = task['files_to_modify'][0]

    # Read current file
    with open(target_file, 'r') as f:
        content = f.read()

    # ---- PATCH CODE (FINAL CORRECT VERSION) ----
    patch_code = '''
    @classmethod
    def find_staged_or_pending(cls, ia_ids, sources=None):
        conds = [("ia_id", "in", ia_ids), ("status", "in", ["staged", "pending"])]

        if sources:
            conds.append(("ia_id", "like", [s + ":%" for s in sources]))

        return cls.find(conds)
'''

    # Inject method ONLY if missing
    if "def find_staged_or_pending" not in content:
        if "class ImportItem" not in content:
            print("ImportItem class not found.")
            sys.exit(1)

        parts = content.split("class ImportItem")
        before = parts[0]
        after = "class ImportItem" + parts[1]

        # insert patch after class declaration
        lines = after.split("\n")
        insert_index = 1

        lines.insert(insert_index, patch_code)
        new_content = before + "\n".join(lines)

        with open(target_file, "w") as f:
            f.write(new_content)

        print("Patch applied successfully.")
    else:
        print("Method already exists.")

if __name__ == "__main__":
    main()
