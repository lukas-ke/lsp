local mega = {
  values = {
    a=1,
    b=2,
    s ="eh"},
  private_functions = {
    f1 = function() return 1 end,
    -- TODO
    f2 = function(a) end
    -- TODO: test trailing comma
    -- TODO: test trailing comma
  },
  more_functions = {
    f3 = function() end,
    f4 = function() end, -- trailing comma!
  }
}

-- Comment for variable
local x = 1
local s = "Some string"

-- apple, banana = 1,2
-- citrus = nil (but declared local)
local apple, banana, citrus = 1, 2

local function f1()
  -- (comment in function)
  return 1
end

local function f2()
  return "str result"
end

function mega.private_functions.mp1() end
function mega.m1(a) end
function mega.m1(a, b) end

g_f = function() end
function g_f2() end

x = mega.more_functions.f3()

return mega
