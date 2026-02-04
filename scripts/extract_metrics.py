#!/usr/bin/env python3
"""
Template for extract_metrics.py - SWE-bench Pro Hackathon
This script extracts metrics from the agent.log and generates result.json
"""

import json
import os
from datetime import datetime
from pathlib import Path

AGENT_LOG_PATH = "/tmp/agent.log"
RESULT_JSON_PATH = "/tmp/result.json"
POST_VERIFICATION_LOG = "/tmp/post_verification.log"

# Claude pricing (as of 2024)
# Input: $3.00 per million tokens
# Output: $15.00 per million tokens
INPUT_COST_PER_TOKEN = 3.00 / 1_000_000
OUTPUT_COST_PER_TOKEN = 15.00 / 1_000_000

def parse_agent_log():
    """Parse the agent.log file to extract metrics"""
    metrics = {
        "input_tokens": 0,
        "output_tokens": 0,
        "tool_usage": {
            "read_file": 0,
            "write_file": 0,
            "edit_file": 0,
            "run_bash": 0
        },
        "start_time": None,
        "end_time": None
    }

    if not os.path.exists(AGENT_LOG_PATH):
        print(f"Warning: {AGENT_LOG_PATH} not found")
        return metrics

    with open(AGENT_LOG_PATH, 'r') as f:
        lines = f.readlines()

    for line in lines:
        try:
            entry = json.loads(line.strip())

            # Track timestamps
            timestamp = entry.get("timestamp")
            if timestamp:
                if metrics["start_time"] is None:
                    metrics["start_time"] = timestamp
                metrics["end_time"] = timestamp

            # Count tool usage
            if entry.get("type") == "tool_use":
                tool_name = entry.get("tool")
                if tool_name in metrics["tool_usage"]:
                    metrics["tool_usage"][tool_name] += 1

            # Estimate tokens (simplified - you may want to use tiktoken for accurate counting)
            if entry.get("type") == "request":
                content = entry.get("content", "")
                # Rough estimate: 1 token per 4 characters
                metrics["input_tokens"] += len(content) // 4

            if entry.get("type") == "response":
                content = entry.get("content", "")
                # Rough estimate: 1 token per 4 characters
                metrics["output_tokens"] += len(content) // 4

        except json.JSONDecodeError:
            print(f"Warning: Failed to parse line: {line[:50]}...")
            continue

    return metrics

def check_test_results():
    """Check if the post-verification tests passed"""
    if not os.path.exists(POST_VERIFICATION_LOG):
        print(f"Warning: {POST_VERIFICATION_LOG} not found")
        return False

    with open(POST_VERIFICATION_LOG, 'r') as f:
        content = f.read()

    # Check for pytest success indicators
    if "PASSED" in content and "FAILED" not in content:
        return True

    # Alternative check for all tests passing
    if "3 passed" in content:  # The task has 3 fail_to_pass tests
        return True

    return False

def calculate_duration(start_time, end_time):
    """Calculate duration in seconds between two ISO timestamps"""
    if not start_time or not end_time:
        return 0

    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration = (end - start).total_seconds()
        return max(0, duration)
    except Exception as e:
        print(f"Error calculating duration: {e}")
        return 0

def generate_result_json():
    """Generate the result.json file with all metrics"""
    # Parse agent log
    metrics = parse_agent_log()

    # Check test results
    resolved = check_test_results()

    # Calculate duration
    duration = calculate_duration(metrics["start_time"], metrics["end_time"])

    # Calculate cost
    total_cost = (
        metrics["input_tokens"] * INPUT_COST_PER_TOKEN +
        metrics["output_tokens"] * OUTPUT_COST_PER_TOKEN
    )

    # Build result dictionary
    result = {
        "resolved": resolved,
        "duration_seconds": duration,
        "total_cost_usd": round(total_cost, 4),
        "tokens": {
            "input": metrics["input_tokens"],
            "output": metrics["output_tokens"],
            "cache_read": 0,  # Not implemented in this template
            "cache_write": 0   # Not implemented in this template
        },
        "tool_usage": {
            "read": metrics["tool_usage"]["read_file"],
            "write": metrics["tool_usage"]["write_file"],
            "edit": metrics["tool_usage"]["edit_file"],
            "bash": metrics["tool_usage"]["run_bash"]
        }
    }

    # Write result.json
    with open(RESULT_JSON_PATH, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Result saved to {RESULT_JSON_PATH}")
    print(json.dumps(result, indent=2))

    return result

def main():
    """Main function"""
    result = generate_result_json()

    # Print summary
    print("\n" + "=" * 50)
    print("EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Task Resolved: {'✅ YES' if result['resolved'] else '❌ NO'}")
    print(f"Duration: {result['duration_seconds']:.2f} seconds")
    print(f"Total Cost: ${result['total_cost_usd']:.4f}")
    print(f"Tokens Used: {result['tokens']['input']} input, {result['tokens']['output']} output")
    print(f"Tool Calls: {sum(result['tool_usage'].values())} total")

if __name__ == "__main__":
    main()