import json

result = json.load(open("/tmp/result.json"))

html = f"""
<html>
<head><title>SWE-bench Dashboard</title></head>
<body>
<h1>SWE-bench Evaluation Result</h1>

<p><b>Resolved:</b> {result["resolved"]}</p>
<p><b>Duration:</b> {result["duration_seconds"]} seconds</p>
<p><b>Total Cost:</b> ${result["total_cost_usd"]}</p>

<h2>Token Usage</h2>
<ul>
<li>Input: {result["tokens"]["input"]}</li>
<li>Output: {result["tokens"]["output"]}</li>
</ul>

</body>
</html>
"""

open("/tmp/dashboard.html","w").write(html)
