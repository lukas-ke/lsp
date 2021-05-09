local util = require("util")
local x, y, z = 1, 2, 3

local f, y = function(x) end, 1
assert(type(f) == "function")
assert(y == 1)

i = 42

local function test()
  return 1, 2
end

a, b = test()

if a == b then
  print("Hello")
end

local function f()
end

local function g()
end

local a, b, c, d = 1, 2, 3
print(a,b)

t1 = { t2 = {} }

t1.x = 2

t1.x, t1.t2.y = 1, 5, 3
assert(t1.x == 1)
assert(t1.t2.y == 5)

x, y, z = 1,2
assert(x == 1)
assert(y == 2)
assert(z == nil)

local function some_func(a,b)
  return a + b
end

print(some_func(1,2))
x,y, = 1, 2
