#!/usr/bin/env python3

import os
import sys
import json
import yaml
from anthropic import Anthropic

def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file",required=True)
    args = parser.parse_args()

    task = yaml.safe_load(open(args.task_file))

    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print("CLAUDE_API_KEY missing")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    task_instruction = f"""
You are an expert software engineer.

{task['description']}

Technical Requirements:
{task['requirements']}

Interface:
{task['interface']}

Files to modify:
{', '.join(task['files_to_modify'])}
"""

    print("Sending task to Claude...")

    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        messages=[
            {"role":"user","content":task_instruction}
        ]
    )

    if response.content and hasattr(response.content[0], "text"):
        print(response.content[0].text)

    print("Claude run complete.")

if __name__=="__main__":
    main()
