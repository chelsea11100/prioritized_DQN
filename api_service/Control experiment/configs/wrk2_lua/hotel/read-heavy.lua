-- StabTune E1: Hotel read-heavy（仅 GET：搜酒店 + 推荐，无写）
local socket = require("socket")
math.randomseed(socket.gettime() * 1000)
math.random()
math.random()
math.random()

local url = "http://127.0.0.1:5000"

local function search_hotel()
  local in_date = math.random(9, 23)
  local out_date = math.random(in_date + 1, 24)
  local in_date_str = in_date <= 9 and ("2015-04-0" .. tostring(in_date)) or ("2015-04-" .. tostring(in_date))
  local out_date_str = out_date <= 9 and ("2015-04-0" .. tostring(out_date)) or ("2015-04-" .. tostring(out_date))
  local lat = 38.0235 + (math.random(0, 481) - 240.5) / 1000.0
  local lon = -122.095 + (math.random(0, 325) - 157.0) / 1000.0
  local path = url .. "/hotels?inDate=" .. in_date_str .. "&outDate=" .. out_date_str ..
    "&lat=" .. tostring(lat) .. "&lon=" .. tostring(lon)
  return wrk.format("GET", path, {}, nil)
end

local function recommend()
  local coin = math.random()
  local req_param = coin < 0.33 and "dis" or (coin < 0.66 and "rate" or "price")
  local lat = 38.0235 + (math.random(0, 481) - 240.5) / 1000.0
  local lon = -122.095 + (math.random(0, 325) - 157.0) / 1000.0
  local path = url .. "/recommendations?require=" .. req_param ..
    "&lat=" .. tostring(lat) .. "&lon=" .. tostring(lon)
  return wrk.format("GET", path, {}, nil)
end

request = function()
  local search_ratio = 0.70
  local coin = math.random()
  if coin < search_ratio then
    return search_hotel()
  end
  return recommend()
end
