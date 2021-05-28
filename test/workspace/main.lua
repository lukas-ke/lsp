local xylophone = 5

-- A **documented** _function_. Have you ever seen anything like this?
-- Kind of spectacular.
--@param a integer Some docs
--@param b string
--@return integer
local function f2(a, b)
  local y = 3
  return 42
end

z = f2(1,2)
--Test
--@return string
local function f3()
  local t = {
    some_number = 1
  }
end

some_global = f3(1)
