# Obscura CDP Domain Coverage

Obscura implements a subset of the Chrome DevTools Protocol. Sufficient for Puppeteer/Playwright basic automation but not a full Chrome CDP replacement.

| Domain | Methods |
|--------|---------|
| **Target** | createTarget, closeTarget, attachToTarget, createBrowserContext, disposeBrowserContext |
| **Page** | navigate, getFrameTree, addScriptToEvaluateOnNewDocument, lifecycleEvents |
| **Runtime** | evaluate, callFunctionOn, getProperties, addBinding |
| **DOM** | getDocument, querySelector, querySelectorAll, getOuterHTML, resolveNode |
| **Network** | enable, setCookies, getCookies, setExtraHTTPHeaders, setUserAgentOverride |
| **Fetch** | enable, continueRequest, fulfillRequest, failRequest (live interception) |
| **Storage** | getCookies, setCookies, deleteCookies |
| **Input** | dispatchMouseEvent, dispatchKeyEvent |
| **LP** | getMarkdown (non-standard: DOM-to-Markdown conversion) |

The `LP.getMarkdown` domain is Obscura-specific — not part of Chrome's CDP spec. Use it for extracting page content as markdown without external tools.
