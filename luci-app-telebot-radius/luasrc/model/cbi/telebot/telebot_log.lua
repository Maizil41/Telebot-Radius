local map = Map("telebot", "")

local status_section = map:section(SimpleSection, "Logs", "")
local status_value = status_section:option(DummyValue, "log_output", "")
status_value.rawhtml = true

-- Membaca isi file log
local log_file = "/tmp/log/telebot.log"
local handle = io.open(log_file, "r")
local log_output = handle and handle:read("*all") or ""
if handle then
    handle:close()
end

status_value.value = [[
    <style>
        .log-output {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ccc;
            padding: 10px;
            background-color: #f9f9f9;
            white-space: pre-wrap;
        }
    </style>
    <div class="log-output">]] .. (log_output or "") .. [[</div>
]]

return map
