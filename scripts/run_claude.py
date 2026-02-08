#!/usr/bin/env python3
import os
import sys
import yaml

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    args = parser.parse_args()

    with open(args.task_file, 'r') as f:
        task = yaml.safe_load(f)

    target_file = task['files_to_modify'][0]

    with open(target_file, 'r') as f:
        content = f.read()

    PATCH = '''
    @classmethod
    def find_staged_or_pending(cls, ia_ids, sources=None):
        from infogami import config

        db = config.db

        conds = []
        params = []

        if ia_ids:
            placeholders = ",".join(["%s"] * len(ia_ids))
            conds.append(f"ia_id IN ({placeholders})")
            params.extend(ia_ids)

        conds.append("status IN ('staged','pending')")

        if sources:
            like_clauses = []
            for s in sources:
                like_clauses.append("ia_id LIKE %s")
                params.append(s + ":%")
            conds.append("(" + " OR ".join(like_clauses) + ")")

        where = " AND ".join(conds)

        rows = db.query(f"SELECT * FROM import_item WHERE {where}", vars=params)

        return list(rows)
'''

    if "def find_staged_or_pending" not in content:
        if "class ImportItem" not in content:
            print("ImportItem class not found.")
            sys.exit(1)

        parts = content.split("class ImportItem")
        before = parts[0]
        after = "class ImportItem" + parts[1]

        lines = after.split("\n")
        lines.insert(1, PATCH)

        new_content = before + "\n".join(lines)

        with open(target_file, "w") as f:
            f.write(new_content)

        print("Patch applied.")
    else:
        print("Method already exists.")

if __name__ == "__main__":
    main()
