-- mock_api.lua
-- Template for mocking API endpoints. Edit the mocks table below.
-- Usage: proxelar --script ~/.claude/skills/proxelar/scripts/mock_api.lua

local mocks = {
    {
        method = "GET",
        pattern = "/api/user/me",
        response = {
            status = 200,
            headers = { ["Content-Type"] = "application/json" },
            body = '{"id": 1, "name": "Test User", "email": "test@example.com"}'
        }
    },
    {
        method = "POST",
        pattern = "/api/auth/login",
        response = {
            status = 200,
            headers = { ["Content-Type"] = "application/json" },
            body = '{"token": "mock-jwt-token-12345", "expires_in": 3600}'
        }
    },
    -- Add more mocks here:
    -- {
    --     method = "GET",
    --     pattern = "/api/items",
    --     response = {
    --         status = 200,
    --         headers = { ["Content-Type"] = "application/json" },
    --         body = '[{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]'
    --     }
    -- },
}

function on_request(request)
    for _, mock in ipairs(mocks) do
        if request.method == mock.method and string.find(request.url, mock.pattern) then
            print(string.format("[MOCK] %s %s -> %d", request.method, mock.pattern, mock.response.status))
            return mock.response
        end
    end
end
