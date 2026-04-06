-- block_telemetry.lua
-- Block analytics, telemetry, and tracking domains during focused development.
-- Usage: proxelar --script ~/.claude/skills/proxelar/scripts/block_telemetry.lua

local blocked_patterns = {
    -- Google
    "google%-analytics%.com",
    "googletagmanager%.com",
    "doubleclick%.net",
    -- Facebook/Meta
    "facebook%.com/tr",
    "connect%.facebook%.net",
    "graph%.facebook%.com",
    -- General analytics
    "segment%.io",
    "segment%.com",
    "mixpanel%.com",
    "amplitude%.com",
    "hotjar%.com",
    "fullstory%.com",
    "sentry%.io",
    "bugsnag%.com",
    -- Ad networks
    "ads%.linkedin%.com",
    "bat%.bing%.com",
    "analytics%.twitter%.com",
    -- Telemetry
    "telemetry%.",
    "tracking%.",
    "collect%.",
}

function on_request(request)
    for _, pattern in ipairs(blocked_patterns) do
        if string.find(request.url, pattern) then
            print(string.format("[BLOCKED] %s %s", request.method, request.url))
            return { status = 204, headers = {}, body = "" }
        end
    end
end
