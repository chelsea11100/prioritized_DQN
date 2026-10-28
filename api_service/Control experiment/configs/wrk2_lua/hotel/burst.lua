-- StabTune E1: Hotel burst（20s 周期内 4s 写突发：登录+预订占比升高）
local socket = require("socket")
math.randomseed(socket.gettime() * 1000)
math.random()
math.random()
math.random()

local url = "http://127.0.0.1:5000"
local burst_cycle_sec = 20
local burst_window_sec = 4

local function get_user()
  local id = math.random(0, 500)
  local user_name = "Cornell_" .. tostring(id)
  local pass_word = ""
  for _ = 0, 9 do
    pass_word = pass_word .. tostring(id)
  end
  return user_name, pass_word
end

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

local function user_login()
  local user_name, password = get_user()
  local path = url .. "/user?username=" .. user_name .. "&password=" .. password
  return wrk.format("POST", path, {}, nil)
end

local function reserve()
  local in_date = math.random(9, 23)
  local out_date = in_date + math.random(1, 5)
  local in_date_str = in_date <= 9 and ("2015-04-0" .. tostring(in_date)) or ("2015-04-" .. tostring(in_date))
  local out_date_str = out_date <= 9 and ("2015-04-0" .. tostring(out_date)) or ("2015-04-" .. tostring(out_date))
  local lat = 38.0235 + (math.random(0, 481) - 240.5) / 1000.0
  local lon = -122.095 + (math.random(0, 325) - 157.0) / 1000.0
  local hotel_id = tostring(math.random(1, 80))
  local user_id, password = get_user()
  local path = url .. "/reservation?inDate=" .. in_date_str .. "&outDate=" .. out_date_str ..
    "&lat=" .. tostring(lat) .. "&lon=" .. tostring(lon) ..
    "&hotelId=" .. hotel_id .. "&customerName=" .. user_id ..
    "&username=" .. user_id .. "&password=" .. password .. "&number=1"
  return wrk.format("POST", path, {}, nil)
end

local function pick_uniform()
  local coin = math.random()
  if coin < 0.60 then
    return search_hotel()
  elseif coin < 0.99 then
    return recommend()
  elseif coin < 0.995 then
    return user_login()
  end
  return reserve()
end

local function pick_burst()
  local coin = math.random()
  if coin < 0.35 then
    return reserve()
  elseif coin < 0.55 then
    return user_login()
  elseif coin < 0.80 then
    return search_hotel()
  end
  return recommend()
end

request = function()
  local phase = math.floor(socket.gettime()) % burst_cycle_sec
  if phase < burst_window_sec then
    return pick_burst()
  end
  return pick_uniform()
end
