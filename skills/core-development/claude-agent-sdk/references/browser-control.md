# Browser Control with Claude Agent SDK

Control web browsers programmatically using the Claude Agent SDK via the Chrome
extension or dev-browser skill. Claude Agent SDK can use Claude Code skills natively.

## Overview: Two Approaches

| Approach | Headless | Persistent State | Best For |
|----------|----------|------------------|----------|
| Chrome Extension | No | Yes (your session) | Interactive testing, auth'd apps |
| dev-browser skill | Optional | Yes (server-managed) | Automation, scripting, E2E tests |

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


## Approach 2: dev-browser Skill (Playwright)

The dev-browser skill provides Playwright-based browser automation with **persistent page state**.
Pages survive script executions - perfect for multi-step workflows.

**Claude Agent SDK can invoke this skill natively.** The skill can be copied into any skills
folder and used by agents directly.

### Installation

The dev-browser skill is available as a marketplace plugin. To use it:

1. Install from marketplace: `~/.claude/plugins/marketplaces/dev-browser-marketplace/`
2. Or copy the skill folder into your project's skills directory

### Setup

Start the dev-browser server:

```bash
./skills/dev-browser/server.sh &
# Wait for "Ready" message
# Use --headless for headless mode
```

Server runs on `http://localhost:9222`.

### Basic Usage

Write inline scripts with heredocs:

```bash
cd skills/dev-browser && bun x tsx <<'EOF'
import { connect, waitForPageLoad } from "@/client.js";

const client = await connect("http://localhost:9222");
const page = await client.page("main"); // get or create a named page

await page.goto("https://example.com");
await waitForPageLoad(page);

const title = await page.title();
console.log({ title, url: page.url() });

await client.disconnect(); // Page stays alive on server
EOF
```

### Client API

```typescript
const client = await connect("http://localhost:9222");
const page = await client.page("name");     // Get or create named page
const pages = await client.list();          // List all page names
await client.close("name");                 // Close a page
await client.disconnect();                  // Disconnect (pages persist)

// ARIA Snapshot for element discovery
const snapshot = await client.getAISnapshot("name");
const element = await client.selectSnapshotRef("name", "e5");
```

### Key Principles

1. **Small scripts**: Each script does ONE thing (navigate, click, fill, check)
2. **Evaluate state**: Always log/return state at the end
3. **Use page names**: Descriptive names like `"checkout"`, `"login"`, `"search-results"`
4. **Disconnect to exit**: Pages persist on server after disconnect

### ARIA Snapshot (Element Discovery)

Use when you don't know the page layout:

```typescript
const snapshot = await client.getAISnapshot("main");
console.log(snapshot);
// Output:
// - banner:
//   - link "Hacker News" [ref=e1]
//   - navigation:
//     - link "new" [ref=e2]
//     - link "submit" [ref=e6]
// ...

// Interact by ref
const element = await client.selectSnapshotRef("main", "e2");
await element.click();
```

### Screenshots

```typescript
await page.screenshot({ path: "tmp/screenshot.png" });
await page.screenshot({ path: "tmp/full.png", fullPage: true });
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

### Pattern 4: dev-browser Workflow Loop

```bash
# 1. Navigate
cd skills/dev-browser && bun x tsx <<'EOF'
import { connect, waitForPageLoad } from "@/client.js";
const client = await connect("http://localhost:9222");
const page = await client.page("test");
await page.goto("https://myapp.com/login");
await waitForPageLoad(page);
console.log("At:", page.url());
await client.disconnect();
EOF

# 2. Discover elements
cd skills/dev-browser && bun x tsx <<'EOF'
import { connect } from "@/client.js";
const client = await connect("http://localhost:9222");
const snapshot = await client.getAISnapshot("test");
console.log(snapshot);
await client.disconnect();
EOF

# 3. Interact
cd skills/dev-browser && bun x tsx <<'EOF'
import { connect } from "@/client.js";
const client = await connect("http://localhost:9222");
const element = await client.selectSnapshotRef("test", "e5");
await element.click();
await client.disconnect();
EOF
```


## Comparison: When to Use What

| Use Case | Chrome Extension | dev-browser |
|----------|------------------|-------------|
| Testing authenticated apps | ✅ (your session) | ❌ (separate browser) |
| Headless automation | ❌ | ✅ (`--headless` flag) |
| Persistent page state | ✅ (Chrome) | ✅ (server-managed) |
| Multiple named pages | ❌ | ✅ |
| CI/CD pipelines | ❌ (needs display) | ✅ |
| Interactive debugging | ✅ | ✅ |
| Visual inspection | ✅ | ✅ (screenshots) |
| ARIA snapshot discovery | ❌ | ✅ |


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

### dev-browser

```typescript
import { connect } from "@/client.js";

const client = await connect("http://localhost:9222");
const page = await client.page("main");

// Debug by taking screenshot and checking state
await page.screenshot({ path: "tmp/debug.png" });
console.log({
  url: page.url(),
  title: await page.title(),
  bodyText: await page.textContent("body").then((t) => t?.slice(0, 200)),
});

await client.disconnect();
```


## Resources

- [Claude Code Chrome Docs](https://code.claude.com/docs/en/chrome)
- [Claude Code Headless Docs](https://code.claude.com/docs/en/headless)
- [Claude in Chrome Extension](https://chromewebstore.google.com/detail/claude-in-chrome)
- dev-browser skill: `~/.claude/plugins/marketplaces/dev-browser-marketplace/`
