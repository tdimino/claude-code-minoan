# Browser Control with Claude Agent SDK

Control web browsers programmatically using the Claude Agent SDK via the Chrome
extension or agent-browser skill. Claude Agent SDK can use Claude Code skills natively.

## Overview: Two Approaches

| Approach | Headless | Persistent State | Best For |
|----------|----------|------------------|----------|
| Chrome Extension | No | Yes (your session) | Interactive testing, auth'd apps |
| agent-browser skill | Default | Yes (session-based) | Automation, scripting, E2E tests |

## Approach 1: Claude Code Chrome Extension

Control your actual Chrome browser via the `--chrome` flag. Uses Native Messaging API.

### Architecture

```
Claude Agent SDK Agent
    ↓ spawns subprocess
Claude Code CLI (claude -p --chrome)
    ↓ Native Messaging API
Chrome Extension (Claude in Chrome v1.0.36+)
    ↓ controls
Your Browser (visible window required)
```

### Prerequisites

- Claude Code CLI v2.0.73+
- Claude in Chrome browser extension (v1.0.36+)
- Paid Claude plan
- Visible browser window (no headless mode)

### From Agent SDK (Python)

```python
import asyncio
import subprocess
import json

async def browser_action(prompt: str) -> dict:
    """Execute a browser action via Claude Code with Chrome."""
    result = subprocess.run(
        [
            "claude", "-p", prompt,
            "--chrome",
            "--output-format", "json",
            "--allowedTools", "Read,Bash"
        ],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Example usage
async def main():
    # Get current browser state
    tabs = await browser_action("What browser tabs are open?")
    print(tabs["result"])

    # Navigate and interact
    await browser_action("Navigate to example.com and click the login button")

    # Read console errors
    errors = await browser_action("What console errors are on this page?")
    print(errors["result"])

asyncio.run(main())
```

### From Agent SDK (TypeScript)

```typescript
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

async function browserAction(prompt: string): Promise<any> {
  const { stdout } = await execAsync(
    `claude -p "${prompt}" --chrome --output-format json`
  );
  return JSON.parse(stdout);
}

// Example: Chain browser actions with SDK logic
async function testLoginFlow() {
  await browserAction("Navigate to https://myapp.com/login");
  await browserAction("Fill the email field with 'test@example.com'");
  await browserAction("Fill the password field with 'password123'");
  await browserAction("Click the submit button");

  const result = await browserAction("Is there a 'Welcome' message on the page?");
  console.log("Login successful:", result.result);
}
```

### Key CLI Flags

| Flag | Purpose |
|------|---------|
| `--chrome` | Enable Chrome extension integration |
| `-p, --print` | Non-interactive mode (required for programmatic use) |
| `--output-format json` | Get structured JSON output |
| `--allowedTools` | Auto-approve specific tools |
| `--max-budget-usd` | Set cost limits |
| `--continue` | Continue conversation context |

### Chrome Capabilities

- Read console errors and DOM state
- Click buttons, fill forms
- Navigate pages
- Take screenshots
- Access authenticated apps (Google Docs, etc.)
- Chain browser actions with terminal commands


## Approach 2: agent-browser Skill (Vercel CLI)

The agent-browser skill provides CLI-based browser automation using Vercel's `agent-browser` tool.
Uses ref-based selection (@e1, @e2) from accessibility snapshots - optimal for LLM agents.

**Claude Agent SDK can invoke this skill natively.** Simple Bash commands instead of scripts.

### Installation

```bash
npm install -g agent-browser
agent-browser install  # Downloads Chromium
```

### Core Workflow

The snapshot + ref pattern is optimal for LLMs:

```bash
# 1. Open URL
agent-browser open https://example.com

# 2. Get interactive elements with refs
agent-browser snapshot -i

# 3. Interact using refs
agent-browser click @e1
agent-browser fill @e2 "search query"

# 4. Re-snapshot after changes
agent-browser snapshot -i
```

### Key Commands

```bash
# Navigation
agent-browser open <url>       # Navigate to URL
agent-browser back             # Go back
agent-browser forward          # Go forward
agent-browser reload           # Reload page
agent-browser close            # Close browser

# Snapshots (essential for AI)
agent-browser snapshot              # Full accessibility tree
agent-browser snapshot -i           # Interactive elements only (recommended)
agent-browser snapshot -i --json    # JSON output for parsing

# Interactions
agent-browser click @e1                    # Click element
agent-browser fill @e1 "text"              # Clear and fill input
agent-browser type @e1 "text"              # Type without clearing
agent-browser press Enter                  # Press key
agent-browser check @e1                    # Check checkbox
agent-browser select @e1 "option"          # Select dropdown option
agent-browser scroll down 500              # Scroll

# Get information
agent-browser get text @e1          # Get element text
agent-browser get html @e1          # Get element HTML
agent-browser get value @e1         # Get input value
agent-browser get title             # Get page title
agent-browser get url               # Get current URL

# Screenshots
agent-browser screenshot                      # Viewport screenshot
agent-browser screenshot --full               # Full page
agent-browser screenshot output.png           # Save to file

# Wait
agent-browser wait @e1              # Wait for element
agent-browser wait 2000             # Wait milliseconds
```

### ARIA Snapshot (Element Discovery)

Interactive elements with refs:

```bash
agent-browser snapshot -i
# Output:
# - button "Submit" [ref=e1]
# - textbox "Email" [ref=e2]
# - link "Sign up" [ref=e3]
```

### Sessions (Parallel Browsers)

```bash
# Run multiple independent browser sessions
agent-browser --session browser1 open https://site1.com
agent-browser --session browser2 open https://site2.com

# List active sessions
agent-browser session list
```

### Debug Mode

```bash
# Run with visible browser window
agent-browser --headed open https://example.com
agent-browser --headed snapshot -i
```


## Patterns & Best Practices

### Pattern 1: Hybrid Agent (Files + Browser)

```python
from claude_agent_sdk import query, ClaudeAgentOptions
import subprocess
import json

async def hybrid_agent():
    # Use SDK for file operations
    async for msg in query(
        prompt="Read the test cases from tests/e2e/login.spec.ts",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Glob"])
    ):
        if hasattr(msg, 'content'):
            test_cases = msg.content

    # Use Chrome for browser testing
    for test in test_cases:
        result = subprocess.run(
            ["claude", "-p", f"Execute this test: {test}", "--chrome", "--output-format", "json"],
            capture_output=True, text=True
        )
        print(json.loads(result.stdout)["result"])
```

### Pattern 2: Screenshot Verification

```python
import subprocess
import json

def verify_design(url: str, expected_elements: list[str]) -> dict:
    """Navigate to URL and verify expected elements are present."""
    result = subprocess.run(
        [
            "claude", "-p",
            f"Navigate to {url} and check if these elements are visible: {expected_elements}",
            "--chrome", "--output-format", "json"
        ],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)
```

### Pattern 3: Authenticated App Testing

```python
async def test_google_docs():
    """Chrome extension uses your logged-in session."""
    await browser_action("Navigate to https://docs.google.com/document/d/YOUR_DOC_ID")
    content = await browser_action("What is the content of this document?")
    print(content["result"])
```

### Pattern 4: agent-browser Workflow Loop

```bash
# 1. Navigate
agent-browser open https://myapp.com/login

# 2. Discover elements
agent-browser snapshot -i
# Shows: textbox "Email" [ref=e1], textbox "Password" [ref=e2], button "Sign in" [ref=e3]

# 3. Interact
agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3

# 4. Verify
agent-browser wait 2000
agent-browser snapshot -i  # Check logged in state
```


## Comparison: When to Use What

| Use Case | Chrome Extension | agent-browser |
|----------|------------------|---------------|
| Testing authenticated apps | ✅ (your session) | ❌ (separate browser) |
| Headless automation | ❌ | ✅ (default) |
| Persistent sessions | ✅ (Chrome) | ✅ (`--session` flag) |
| Multiple parallel browsers | ❌ | ✅ (named sessions) |
| CI/CD pipelines | ❌ (needs display) | ✅ |
| Interactive debugging | ✅ | ✅ (`--headed` flag) |
| Visual inspection | ✅ | ✅ (screenshots) |
| ARIA snapshot discovery | ❌ | ✅ |
| Simple Bash-based workflow | ❌ | ✅ |


## Error Handling

### Chrome Extension

```python
import subprocess
import json

def safe_browser_action(prompt: str, timeout: int = 60) -> dict:
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--chrome", "--output-format", "json"],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return {"error": result.stderr, "success": False}
        parsed = json.loads(result.stdout)
        return {"result": parsed["result"], "success": True}
    except subprocess.TimeoutExpired:
        return {"error": "Browser action timed out", "success": False}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response: {e}", "success": False}
```

### agent-browser

```bash
# Debug by taking screenshot and checking state
agent-browser screenshot debug.png
agent-browser get url
agent-browser get title

# Get JSON output for structured debugging
agent-browser snapshot -i --json
```


## Resources

- [Claude Code Chrome Docs](https://code.claude.com/docs/en/chrome)
- [Claude Code Headless Docs](https://code.claude.com/docs/en/headless)
- [Claude in Chrome Extension](https://chromewebstore.google.com/detail/claude-in-chrome)
- [Vercel agent-browser](https://github.com/vercel/agent-browser)
- agent-browser skill: `~/.claude/skills/agent-browser/`
