-- latency_inject.lua
-- Add artificial latency to matching URLs for timeout and resilience testing.
-- Edit the rules table to configure which endpoints get delayed.
-- Usage: proxelar --script ~/.claude/skills/proxelar/scripts/latency_inject.lua

local rules = {
    { pattern = "/api/", delay_ms = 500 },    -- 500ms delay on all /api/ routes
    -- { pattern = "/slow", delay_ms = 3000 },  -- 3s delay on /slow endpoints
    -- { pattern = ".", delay_ms = 100 },        -- 100ms on everything (uncomment for global)
}

local function sleep_ms(ms)
    -- Lua os.execute-based sleep (resolution ~1ms on macOS)
    os.execute(string.format("sleep %.3f", ms / 1000))
end

function on_request(request)
    for _, rule in ipairs(rules) do
        if string.find(request.url, rule.pattern) then
            print(string.format("[LATENCY] +%dms %s %s", rule.delay_ms, request.method, request.url))
            sleep_ms(rule.delay_ms)
            return request
        end
    end
end
