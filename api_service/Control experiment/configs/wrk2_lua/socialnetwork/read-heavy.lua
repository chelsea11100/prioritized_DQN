-- StabTune E1: SocialNetwork read-heavy（100% 读时间线）
local socket = require("socket")
math.randomseed(socket.gettime() * 1000)
math.random()
math.random()
math.random()

local max_user_index = tonumber(os.getenv("max_user_index")) or 962

local function read_home_timeline()
  local user_id = tostring(math.random(0, max_user_index - 1))
  local start = tostring(math.random(0, 100))
  local stop = tostring(tonumber(start) + 10)
  local args = "user_id=" .. user_id .. "&start=" .. start .. "&stop=" .. stop
  local path = "http://127.0.0.1:8080/wrk2-api/home-timeline/read?" .. args
  return wrk.format("GET", path, { ["Content-Type"] = "application/x-www-form-urlencoded" }, nil)
end

local function read_user_timeline()
  local user_id = tostring(math.random(0, max_user_index - 1))
  local start = tostring(math.random(0, 100))
  local stop = tostring(tonumber(start) + 10)
  local args = "user_id=" .. user_id .. "&start=" .. start .. "&stop=" .. stop
  local path = "http://127.0.0.1:8080/wrk2-api/user-timeline/read?" .. args
  return wrk.format("GET", path, { ["Content-Type"] = "application/x-www-form-urlencoded" }, nil)
end

request = function()
  if math.random() < 0.5 then
    return read_home_timeline()
  end
  return read_user_timeline()
end
