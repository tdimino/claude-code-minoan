# Proxelar Lua Scripting API Reference

## Hook Functions

### `on_request(request) -> request | response | nil`

Fires before forwarding a request upstream.

**`request` object:**
| Field | Type | Description |
|-------|------|-------------|
| `method` | string | HTTP method (GET, POST, PUT, etc.) |
| `url` | string | Full request URL |
| `headers` | table | Request headers (key-value pairs) |
| `body` | string/nil | Request body (nil for bodiless methods) |

**Return values:**
- Return the `request` (modified or not) to forward it upstream
- Return a `response` table to short-circuit (mock the response):
  ```lua
  return { status = 200, headers = { ["Content-Type"] = "application/json" }, body = '{"ok": true}' }
  ```
- Return `nil` to pass through unchanged

### `on_response(request, response) -> response | nil`

Fires after receiving a response from upstream, before sending to client.

**`response` object:**
| Field | Type | Description |
|-------|------|-------------|
| `status` | number | HTTP status code |
| `headers` | table | Response headers (key-value pairs) |
| `body` | string/nil | Response body |

**Return values:**
- Return the `response` (modified or not) to send to client
- Return `nil` to pass through unchanged

## Common Patterns

### Block requests matching a pattern
```lua
function on_request(request)
    if string.find(request.url, "blocked%.example%.com") then
        return { status = 403, headers = {}, body = "Blocked" }
    end
end
```

### Modify response headers
```lua
function on_response(request, response)
    response.headers["X-Custom-Header"] = "injected"
    return response
end
```

### Modify JSON response body
```lua
function on_response(request, response)
    if string.find(request.url, "/api/data") then
        -- Proxelar embeds Lua 5.4 in safe mode (no C modules like cjson).
        -- Use string manipulation for JSON transforms:
        response.body = response.body:gsub('"old_value"', '"new_value"')
        return response
    end
end
```

### Log to stdout
```lua
function on_response(request, response)
    print(string.format("[%d] %s %s", response.status, request.method, request.url))
    return response
end
```

### File I/O
```lua
local f = io.open("/path/to/file", "a")
f:write("data\n")
f:close()
```

## Limitations

- Scripts load once at proxy startup; changes require restart
- Lua 5.4 in safe mode — standard library only, C module loading (`require("cjson")` etc.) is disabled
- In `on_response`, `request.headers` and `request.body` are `nil` — only `request.method` and `request.url` are available. Use `on_request` to capture request headers/body before forwarding.
- `response.headers` is a writable table in `on_response`; `response.body` and `response.status` are available
- WebSocket frames are not intercepted by Lua hooks
- `on_request` runs synchronously; blocking calls (like `os.execute("sleep")`) delay the request
