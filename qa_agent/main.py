import json
import os
import requests
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Tools ---

def read_playwright_results(path: str) -> dict:
    """Reads the Playwright JSON results file and returns a summary."""
    if not os.path.exists(path):
        return {"error": f"File not found: {path}"}

    with open(path) as f:
        results = json.load(f)

    total = results.get("stats", {})
    failed = [
        t for suite in results.get("suites", [])
        for t in suite.get("specs", [])
        if not t.get("ok")
    ]
    return {
        "total": total,
        "failed_tests": [t["title"] for t in failed[:10]]
    }


def post_pr_comment(comment: str) -> str:
    """Posts a comment on a GitHub PR."""
    token = os.getenv("GH_TOKEN")
    repo  = os.getenv("GITHUB_REPO")
    pr    = os.getenv("PR_NUMBER")

    if not all([token, repo, pr]):
        return "Error: GH_TOKEN, GITHUB_REPO or PR_NUMBER environment variables are not set."

    url  = f"https://api.github.com/repos/{repo}/issues/{pr}/comments"
    resp = requests.post(
        url,
        json={"body": comment},
        headers={"Authorization": f"Bearer {token}"}
    )
    return "Comment posted!" if resp.status_code == 201 else f"Error: {resp.status_code} - {resp.text}"


# --- Agent 1: Analyst ---

def analyze_results(file_path: str) -> str:
    """Uses Claude to analyze test results."""
    data = read_playwright_results(file_path)

    if "error" in data:
        return f"Failed to read file: {data['error']}"

    prompt = f"""You are a senior QA engineer with 10 years of experience.
Analyze the following Playwright test results and identify:
- Total tests run, passed, and failed
- Critical failures
- Error patterns
- Severity level (low / medium / high / critical)

Test results:
{json.dumps(data, indent=2)}

Respond with a structured JSON containing: total, passed, failed, severity, failures, patterns.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# --- Agent 2: Writer ---

def generate_and_post_report(analysis: str) -> str:
    """Uses Claude to turn the analysis into a PR comment and posts it to GitHub."""

    prompt = f"""You are a technical writer who creates clear reports for developers and product managers.
Based on the QA analysis below, write a professional GitHub PR comment in markdown.

The comment should include:
- A clear summary with emoji indicators (✅ ❌ ⚠️)
- A table of failed tests with severity
- Identified error patterns
- A suggested next step

QA Analysis:
{analysis}

Write only the markdown comment, nothing else.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    comment = response.choices[0].message.content
    print("\n--- Generated comment ---")
    print(comment)
    print("-------------------------\n")

    return post_pr_comment(comment)


# --- Main execution ---

if __name__ == "__main__":
    file_path = "playwright-report/results.json"

    print("🔍 Analyzing test results...")
    analysis = analyze_results(file_path)
    print("Analysis complete.")
    print(analysis)

    print("\n📝 Generating and posting report to PR...")
    result = generate_and_post_report(analysis)
    print(result)