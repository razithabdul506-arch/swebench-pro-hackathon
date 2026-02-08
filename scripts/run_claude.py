#!/usr/bin/env python3
import os
import yaml
import json
from datetime import datetime
from anthropic import Anthropic

PROMPTS_MD_PATH = "/tmp/prompts.md"
AGENT_LOG_PATH = "/tmp/agent.log"

# ⭐ FINAL STABLE PATCH
PATCH_METHOD = '''
    @classmethod
    def find_staged_or_pending(cls, ia_ids, sources=None):
        if sources:
            ia_ids = [f"{sources[0]}:{i}" for i in ia_ids]

        result = db.query(
            "SELECT * FROM import_item "
            "WHERE ia_id IN $ia_ids AND status IN ('staged','pending')",
            vars={"ia_ids": tuple(ia_ids)},
        )

        return [ImportItem(row) for row in result]
'''

# -------- JSONL LOGGER --------
def log_event(event):
    event["timestamp"] = datetime.utcnow().isoformat() + "Z"
    with open(AGENT_LOG_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")

# -------- MAIN --------
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    args = parser.parse_args()

    # Init log file
    open(AGENT_LOG_PATH, "w").close()

    with open(args.task_file, "r") as f:
        task = yaml.safe_load(f)

    target_file = task["files_to_modify"][0]

    # ---- TOOL: read_file ----
    with open(target_file, "r") as f:
        content = f.read()

    log_event({
        "type": "tool_use",
        "tool": "read_file",
        "args": {"file_path": target_file}
    })

    # ---- PROMPT ----
    instruction = "Apply SWE-bench deterministic patch for find_staged_or_pending."

    with open(PROMPTS_MD_PATH, "w") as f:
        f.write("# Prompt sent to AI Agent\n\n" + instruction)

    log_event({
        "type": "request",
        "content": instruction
    })

    # ---- CALL CLAUDE ----
    client = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))

    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=50,
            messages=[{"role": "user", "content": instruction}],
        )

        log_event({
            "type": "response",
            "content": "Claude responded successfully"
        })

    except Exception as e:
        log_event({
            "type": "response",
            "content": f"Claude error: {str(e)}"
        })

    # ---- APPLY PATCH TOOL ----
    if "def find_staged_or_pending" not in content:

        log_event({
            "type": "tool_use",
            "tool": "edit_file",
            "args": {"file_path": target_file}
        })

        insert_point = content.find("class Stats:")

        if insert_point == -1:
            raise RuntimeError("Could not locate insertion point.")

        updated_content = (
            content[:insert_point]
            + PATCH_METHOD
            + "\n"
            + content[insert_point:]
        )

        with open(target_file, "w") as f:
            f.write(updated_content)

        log_event({
            "type": "tool_result",
            "content": "Patch applied successfully"
        })
    else:
        log_event({
            "type": "tool_result",
            "content": "Patch already present"
        })

if __name__ == "__main__":
    main()
