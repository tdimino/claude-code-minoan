-- capture_for_eval.lua
-- Capture LLM API request/response pairs as structured JSONL for eval datasets.
-- Intercepts calls to Anthropic, OpenAI, and Google Gemini APIs.
-- Usage: proxelar --script ~/.claude/skills/proxelar/scripts/capture_for_eval.lua

local log_path = os.getenv("HOME") .. "/.proxelar/llm_captures.jsonl"

local api_patterns = {
    { pattern = "api%.anthropic%.com", provider = "anthropic" },
    { pattern = "api%.openai%.com", provider = "openai" },
    { pattern = "generativelanguage%.googleapis%.com", provider = "gemini" },
    { pattern = "openrouter%.ai/api", provider = "openrouter" },
}

local function escape_json(s)
    if not s then return "" end
    -- Escape all control characters (0x00-0x1F), backslash, and double quote
    return s:gsub('[%z\1-\31\\"]', function(c)
        local replacements = { ['\\'] = '\\\\', ['"'] = '\\"', ['\n'] = '\\n', ['\r'] = '\\r', ['\t'] = '\\t' }
        return replacements[c] or string.format('\\u%04x', string.byte(c))
    end)
end

local function match_provider(url)
    for _, api in ipairs(api_patterns) do
        if string.find(url, api.pattern) then
            return api.provider
        end
    end
    return nil
end

function on_response(request, response)
    local provider = match_provider(request.url)
    if not provider then return response end

    local f = io.open(log_path, "a")
    if f then
        -- Note: request.body is nil in on_response; capture response body only
        local entry = string.format(
            '{"ts":"%s","provider":"%s","method":"%s","url":"%s","status":%d,"response_body":"%s"}',
            os.date("!%Y-%m-%dT%H:%M:%SZ"),
            provider,
            escape_json(request.method),
            escape_json(request.url),
            response.status,
            escape_json(response.body or "")
        )
        f:write(entry .. "\n")
        f:close()
        print(string.format("[CAPTURE] %s %s %d", provider, request.url, response.status))
    end
    return response
end
