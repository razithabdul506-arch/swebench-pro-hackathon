#!/usr/bin/env python3
import yaml
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    args = parser.parse_args()

    # Load task.yaml
    with open(args.task_file, "r") as f:
        task = yaml.safe_load(f)

    target_file = task["files_to_modify"][0]

    print("Patching file:", target_file)

    # Read file
    with open(target_file, "r") as f:
        content = f.read()

    # If already patched, exit safely
    if "def find_staged_or_pending" in content:
        print("Method already exists. Skipping.")
        return

    # Inject fix inside ImportItem class
    patch_code = '''
    @classmethod
    def find_staged_or_pending(cls, ia_ids, sources=None):
        from infogami.queries import ResultSet

        conds = [("ia_id", "in", ia_ids), ("status", "in", ["staged", "pending"])]

        if sources:
            conds.append(("ia_id", "like", [s + ":%" for s in sources]))

        items = cls.find(conds)
        return ResultSet(items)
'''

    # Insert after class ImportItem declaration
    lines = content.splitlines()
    new_lines = []
    inserted = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        if not inserted and line.strip().startswith("class ImportItem"):
            # Find next indentation block
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("class "):
                    break
                if lines[j].startswith("    def") or lines[j].startswith("    @"):
                    new_lines.append(patch_code)
                    inserted = True
                    break

    if not inserted:
        new_lines.append(patch_code)

    new_content = "\n".join(new_lines)

    # Write file
    with open(target_file, "w") as f:
        f.write(new_content)

    # Required artifact for SWE-bench
    with open("/tmp/prompts.md", "w") as f:
        f.write("Manual patch applied for ImportItem.find_staged_or_pending")

    print("Patch applied successfully.")

if __name__ == "__main__":
    main()
