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

    task = yaml.safe_load(open(args.task_file))

    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print("Missing CLAUDE_API_KEY")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    prompt = f"""
You are an expert SWE-bench engineer.

Task Description:
{task['description']}

Requirements:
{task['requirements']}

Interface:
{task['interface']}

Files:
{', '.join(task['files_to_modify'])}
"""

    print("Sending task to Claude...")

    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    print(response.content[0].text)

if __name__ == "__main__":
    main()
