#!/usr/bin/env python3

import os
import sys
import json
import yaml
import subprocess
from datetime import datetime, UTC
from typing import Dict, Any

from anthropic import Anthropic

AGENT_LOG_PATH = "/tmp/agent.log"
PROMPTS_PATH = "/tmp/prompts.md"


# ================= LOGGING =================
def log_to_agent(entry: Dict[str, Any]):
    entry["timestamp"] = datetime.now(UTC).isoformat()

    with open(AGENT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # readable prompts.md
    try:
        with open(PROMPTS_PATH, "a") as md:
            if entry["type"] == "request":
                md.write("\n## 🧠 Prompt Sent to Claude\n\n")
                md.write(entry["content"] + "\n")
            elif entry["type"] == "response":
                md.write("\n## 🤖 Claude Response\n\n")
                md.write(entry["content"] + "\n")
            elif entry["type"] == "tool_use":
                md.write(f"\n## 🛠️ Tool Used: {entry.get('tool')}\n")
                md.write(json.dumps(entry.get("args", {}), indent=2) + "\n")
    except:
        pass


# ================= TOOLS =================
def read_file(file_path: str):
    try:
        content = open(file_path).read()
        log_to_agent({"type": "tool_use","tool":"read_file","args":{"file_path":file_path}})
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

def write_file(file_path: str, content: str):
    try:
        open(file_path,"w").write(content)
        log_to_agent({"type":"tool_use","tool":"write_file","args":{"file_path":file_path}})
        return {"success": True}
    except Exception as e:
        return {"success": False,"error":str(e)}

def edit_file(file_path: str, old_text: str, new_text: str):
    try:
        text = open(file_path).read()
        new_content = text.replace(old_text,new_text,1)
        open(file_path,"w").write(new_content)
        log_to_agent({"type":"tool_use","tool":"edit_file","args":{"file_path":file_path}})
        return {"success": True}
    except Exception as e:
        return {"success": False,"error":str(e)}

def run_bash(command: str):
    result = subprocess.run(command,shell=True,capture_output=True,text=True)
    log_to_agent({"type":"tool_use","tool":"run_bash","args":{"command":command}})
    return {"stdout":result.stdout,"stderr":result.stderr,"returncode":result.returncode}


def execute_tool(name,args):
    if name=="read_file": return read_file(**args)
    if name=="write_file": return write_file(**args)
    if name=="edit_file": return edit_file(**args)
    if name=="run_bash": return run_bash(**args)
    return {"error":"unknown tool"}


# ================= MAIN =================
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

    log_to_agent({"type":"request","content":task_instruction})

    messages=[{"role":"user","content":task_instruction}]

    tools=[
        {"name":"read_file","input_schema":{"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}},
        {"name":"write_file","input_schema":{"type":"object","properties":{"file_path":{"type":"string"},"content":{"type":"string"}},"required":["file_path","content"]}},
        {"name":"edit_file","input_schema":{"type":"object","properties":{"file_path":{"type":"string"},"old_text":{"type":"string"},"new_text":{"type":"string"}},"required":["file_path","old_text","new_text"]}},
        {"name":"run_bash","input_schema":{"type":"object","properties":{"command":{"type":"string"}},"required":["command"]}}
    ]

    for _ in range(30):

        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=8192,
            messages=messages,
            tools=tools
        )

        text = ""
        if response.content and hasattr(response.content[0], "text"):
            text = response.content[0].text

        log_to_agent({"type":"response","content":text})

        if response.stop_reason=="tool_use":
            tool_call=response.content[-1]
            result=execute_tool(tool_call.name,tool_call.input)

            messages.append({"role":"assistant","content":response.content})
            messages.append({
                "role":"user",
                "content":[{"type":"tool_result","tool_use_id":tool_call.id,"content":json.dumps(result)}]
            })
        else:
            break

    print("Claude run complete.")


if __name__=="__main__":
    main()
