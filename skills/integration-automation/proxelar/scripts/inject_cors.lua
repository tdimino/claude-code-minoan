-- inject_cors.lua
-- Add permissive CORS headers to all responses.
-- Useful when developing frontends against APIs that don't set CORS headers.
-- Usage: proxelar --script ~/.claude/skills/proxelar/scripts/inject_cors.lua

local function cors_origin(request)
    return request.headers["Origin"] or request.headers["origin"] or "*"
end

function on_request(request)
    -- Handle preflight OPTIONS requests by reflecting the requested method/headers
    if request.method == "OPTIONS" then
        local allow_headers = request.headers["Access-Control-Request-Headers"]
            or request.headers["access-control-request-headers"]
            or "Content-Type, Authorization, X-Requested-With"
        local allow_method = request.headers["Access-Control-Request-Method"]
            or request.headers["access-control-request-method"]
            or "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        return {
            status = 204,
            headers = {
                ["Access-Control-Allow-Origin"] = cors_origin(request),
                ["Access-Control-Allow-Methods"] = allow_method,
                ["Access-Control-Allow-Headers"] = allow_headers,
                ["Access-Control-Allow-Credentials"] = "true",
                ["Access-Control-Max-Age"] = "86400",
            },
            body = ""
        }
    end
end

function on_response(request, response)
    response.headers["Access-Control-Allow-Origin"] = cors_origin(request)
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response
end
