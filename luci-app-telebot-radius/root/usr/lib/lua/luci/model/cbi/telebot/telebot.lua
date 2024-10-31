local map = Map("telebot", "")

local status_section = map:section(SimpleSection, "Status", "")
local status_value = status_section:option(DummyValue, "status", "")
status_value.rawhtml = true

local status_command = "/etc/telebot/telebot.sh"
local handle = io.popen(status_command)
local status_output = handle:read("*all")
handle:close()

status_output = status_output or ""

if string.find(status_output, "Bot is running") then
    status_value.value = '<p><strong><span style="color:green;"><i>Telebot RUNNING</i></span></strong></p>'
else
    status_value.value = '<p><strong><span style="color:red;"><i>Telebot NOT RUNNING</i></span></strong></p>'
end

local sec = map:section(TypedSection, "telebot", "Settings")
sec.addremove = false
sec.anonymous = true

local enabled = sec:option(Flag, "enabled", "Enabled")
enabled.default = 0
enabled.optional = false

local token = sec:option(Value, "token", "Bot Token")
token.default = ""
token.placeholder = "Enter your bot token"

local userid = sec:option(Value, "userid", "User ID")
userid.default = ""
userid.placeholder = "Enter your user ID"

local username = sec:option(Value, "username", "Username")
username.default = ""
username.placeholder = "Enter your username"

local ip_chilli = sec:option(Value, "ip_chilli", "IP Chilli")
ip_chilli.default = ""
ip_chilli.placeholder = "Enter your Chilli IP"

local ip_lan = sec:option(Value, "ip_lan", "IP Lan")
ip_lan.default = ""
ip_lan.placeholder = "Enter your Lan IP"

local ticket_loc = sec:option(Value, "ticket_loc", "PrintTickets")
ticket_loc.default = "/RadiusMonitor/dist/pages/data/printTickets1.php"
ticket_loc.placeholder = "PrintTickets Location"

local geocode = sec:option(Value, "geocode", "Location Address")
geocode.default = ""
geocode.placeholder = "latitude,longitude"

local no_ewallet = sec:option(Value, "no_ewallet", "Nomor E-Wallet")
no_ewallet.default = ""
no_ewallet.placeholder = "Enter your ewallet Number"

local apply = luci.http.formvalue("cbi.apply")
if apply then
	os.execute("/etc/init.d/telebot restart >/dev/null 2>&1 &")
end

return map
