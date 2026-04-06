-- log_to_jsonl.lua
-- Log all HTTP request/response pairs as JSONL to ~/.proxelar/traffic.jsonl
-- Usage: proxelar --script ~/.claude/skills/proxelar/scripts/log_to_jsonl.lua

local log_path = os.getenv("HOME") .. "/.proxelar/traffic.jsonl"

local function escape_json(s)
    if not s then return "" end
    return s:gsub('[%z\1-\31\\"]', function(c)
        local replacements = { ['\\'] = '\\\\', ['"'] = '\\"', ['\n'] = '\\n', ['\r'] = '\\r', ['\t'] = '\\t' }
        return replacements[c] or string.format('\\u%04x', string.byte(c))
    end)
end

local function headers_to_json(headers)
    if not headers then return "{}" end
    local parts = {}
    for k, v in pairs(headers) do
        table.insert(parts, string.format('"%s":"%s"', escape_json(tostring(k)), escape_json(tostring(v))))
    end
    return "{" .. table.concat(parts, ",") .. "}"
end

function on_response(request, response)
    local f = io.open(log_path, "a")
    if f then
        local entry = string.format(
            '{"ts":"%s","method":"%s","url":"%s","status":%d,"res_headers":%s,"req_body_len":%d,"res_body_len":%d}',
            os.date("!%Y-%m-%dT%H:%M:%SZ"),
            escape_json(request.method),
            escape_json(request.url),
            response.status,
            headers_to_json(response.headers),
            request.body and #request.body or 0,
            response.body and #response.body or 0
        )
        f:write(entry .. "\n")
        f:close()
    end
    return response
end
