# 🤖 QA Agent — Automated Test Analysis with AI

An intelligent QA agent that automatically analyzes Playwright test failures and posts detailed reports as GitHub PR comments — powered by Claude and CrewAI.

---

## How it works

```
Playwright Tests fail
        ↓
GitHub Actions triggers QA Agent
        ↓
 Analyst Agent reads test results
        ↓
 Writer Agent generates PR report
        ↓
Comment posted automatically on PR
```

Two AI agents collaborate in sequence:

- **QA Analyst** — reads the Playwright JSON output, identifies critical failures, detects error patterns, and scores severity
- **Technical Writer** — transforms the raw analysis into a clear, professional PR comment that both devs and POs can understand

---

## Tech stack

| Layer | Tool |
|---|---|
| Test runner | [Playwright](https://playwright.dev) |
| Agent framework | [CrewAI](https://crewai.com) |
| LLM | [Claude](https://anthropic.com) via `langchain-anthropic` |
| CI/CD | GitHub Actions |

---

## Project structure

```
.
├── .github/
│   └── workflows/
│       ├── playwright.yml      # runs tests on push/PR
│       └── qa-agent.yml        # triggers on test failure
├── qa_agent/
│   └── main.py                 # agent definition and execution
├── tests/
│   └── example.spec.ts         # Playwright test specs
├── playwright.config.ts
├── requirements.txt
└── .env                        # local only — never commit
```

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/andrezaraquel/qa-agent.git
cd qa-agent

# Python
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Node / Playwright
npm install
npx playwright install --with-deps
```

### 2. Configure environment variables

Create a `.env` file at the root:

```env
ANTHROPIC_API_KEY=sk-ant-...
GH_TOKEN=ghp_...
GITHUB_REPO=your-org/your-repo
PR_NUMBER=123
```

### 3. Add GitHub Secrets

Go to your repository → **Settings → Security → Secrets and variables → Actions** and add:

| Secret | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GH_TOKEN` | Your GitHub Personal Access Token |

---

## Running locally

```bash
# Run Playwright tests
npx playwright test

# Run the QA agent manually (after tests generate a report)
python qa_agent/main.py
```

---

## How the automation triggers

The `qa-agent.yml` workflow only runs when the `Playwright Tests` workflow **fails**. On success, nothing happens — no noise, no unnecessary API calls.

```
push to main/PR → Playwright Tests
                        ↓ (only on failure)
                   QA Agent Report
                        ↓
                  Comment on PR ✅
```

---

## Example PR comment

> **🔴 QA Report — 3 failures detected**
>
> | Test | Status | Severity |
> |---|---|---|
> | `login > should redirect on success` | ❌ Failed | High |
> | `checkout > payment form renders` | ❌ Failed | Medium |
>
> **Pattern identified:** Both failures share a missing `data-testid` attribute, likely caused by a recent component refactor.
>
> **Suggested next step:** Check the `AuthForm` and `PaymentField` components for removed or renamed attributes.

---
