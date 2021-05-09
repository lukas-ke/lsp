local function f1(x)
  return x + 1
end

local f2 = function(x)
  return x * 2
end

local f3 = f1

function g_f1(y)
end

return f3
